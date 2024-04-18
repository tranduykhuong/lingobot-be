import logging
from datetime import datetime, timedelta
from itertools import chain

import pytz
import os
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import (csrf_exempt, csrf_protect,
                                          ensure_csrf_cookie)
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payment import models as payment_models
from payment import serializers as payment_serializers
from api import exceptions
from api.services.stripe import STRIPE_EVENTS, stripe
from api.services.mail import MailService

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        methods=["POST"],
        operation_description="Create Checkout Session",
        request_body=payment_serializers.CheckoutDeserializer,
        responses={
            200: payment_serializers.CheckoutSerializer(many=False),
            400: "Bad Request",
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        serializer_class=payment_serializers.CheckoutDeserializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = payment_serializers.CheckoutDeserializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            subscription_cur = (
                payment_models.SubscriptionAuthUser.get_current_subscription_plan(
                    request.user.id
                )
            )
            subscription_plan = payment_models.SubscriptionPlan.objects.get(
                id=serializer.data["subscription_plan_id"]
            )
        except Exception as e:
            raise exceptions.InvalidSubscription

        if subscription_cur.subscription_plan.name in (
            payment_models.SubscriptionPlan.PREMIUM,
        ):
            raise exceptions.SubscriptionBeingValid

        result = payment_models.SubscriptionAuthUser.create_checkout_session(
            request.user.id, **serializer.data
        )
        result = payment_serializers.CheckoutSerializer(result).data

        if not result:
            raise exceptions.ErrorCreateCheckoutSession

        return Response(data=result, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body.decode("utf-8")
        sig_header = request.headers.get("Stripe-Signature")

        try:
            print(os.getenv('STRIPE_ENDPOINT_SECRET'))
            event = stripe.Webhook.construct_event(
                payload, sig_header, os.getenv('STRIPE_ENDPOINT_SECRET')
            )

        except ValueError as e:
            return JsonResponse({"error": "Invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({"error": f"Invalid signature: {e}"}, status=400)

        try:
            if event["type"] == STRIPE_EVENTS["CHECKOUT_SESSION_COMPLETED"]:
                user_id = event["data"]["object"]["client_reference_id"]
                stripe_subscription_id = event["data"]["object"]["subscription"]
                invoice_id = event["data"]["object"]["invoice"]
                price_id = event["data"]["object"]["metadata"]["price_id"]

                user = payment_models.SubscriptionAuthUser.objects.get(id=user_id)
                subscription_plan = payment_models.SubscriptionPlan.objects.filter(
                    stripe_price_id=price_id
                ).first()

                # Start time default by subscription_plan
                start_day = timezone.now()
                end_day = start_day + timedelta(days=subscription_plan.duration * 30)

                # Start time with subscription stripe
                if stripe_subscription_id is not None:
                    subscription_stripe = stripe.Subscription.retrieve(
                        stripe_subscription_id
                    )
                    start_day = timezone.make_aware(
                        datetime.utcfromtimestamp(subscription_stripe["current_period_start"]),
                        timezone=pytz.timezone(settings.TIME_ZONE)
                    )
                    end_day = timezone.make_aware(
                        datetime.utcfromtimestamp(subscription_stripe["current_period_end"]),
                        timezone=pytz.timezone(settings.TIME_ZONE)
                    )

                # Check if the old subscription has not expired then new start_time = old end_time
                subscription_cur = (
                    payment_models.SubscriptionAuthUser.get_current_subscription_plan(
                        user_id
                    )
                )
                if (
                    subscription_cur.subscription_plan.name
                    != payment_models.SubscriptionPlan.FREE
                    and subscription_plan.duration > 1
                ):
                    start_day = subscription_cur.end_day
                    end_day = start_day + timedelta(
                        days=subscription_plan.duration * 30
                    )

                status = payment_models.SubscriptionHistory.INACTIVE
                if (
                    start_day <= timezone.now()
                    and end_day >= timezone.now()
                ):
                    status = payment_models.SubscriptionHistory.ACTIVE

                subscription_history = (
                    payment_models.SubscriptionHistory.objects.create(
                        user=user,
                        subscription_plan=subscription_plan,
                        payment_status=payment_models.SubscriptionHistory.SUCCESS
                        if event["data"]["object"]["payment_status"] == "paid"
                        else None,
                        stripe_subscription_id=stripe_subscription_id,
                        start_day=start_day,
                        end_day=end_day,
                        auto_renew=subscription_plan.duration == 1,
                        status=status,
                    )
                )
                subscription_history.save()

                invoice_stripe = payment_models.SubscriptionAuthUser.get_invoice(
                    invoice_id
                )

                invoice = payment_models.Invoice.objects.create(
                    user=user,
                    subscription_history=subscription_history,
                    stripe_invoice_id=invoice_id,
                    hosted_invoice_url=invoice_stripe["hosted_invoice_url"],
                )
                invoice.save()

                MailService.send_mail_subscription_success(
                    user, subscription_plan, subscription_history, invoice_stripe
                )

            elif event["type"] == STRIPE_EVENTS["CUSTOMER_SUBSCRIPTION_UPDATE"]:
                subscription_stripe_id = event["data"]["object"]["id"]
                latest_invoice = event["data"]["object"]["latest_invoice"]

                invoice_stripe = payment_models.SubscriptionAuthUser.get_invoice(
                    latest_invoice
                )

                subscription_history = (
                    payment_models.SubscriptionHistory.objects.filter(
                        stripe_subscription_id=subscription_stripe_id
                    ).first()
                )
                user = payment_models.SubscriptionAuthUser.objects.filter(
                    id=subscription_history.user_id
                ).first()

                if subscription_history:
                    end_day = timezone.make_aware(
                        datetime.utcfromtimestamp(event["data"]["object"]["current_period_end"]),
                        timezone=pytz.timezone(settings.TIME_ZONE)
                    )
                    subscription_history.subscription_type = (
                        subscription_history.RESUBSCRIPTION
                    )
                    subscription_history.end_day = end_day
                    subscription_history.save()

                try:
                    existed_invoice = payment_models.Invoice.objects.get(
                        stripe_invoice_id=latest_invoice
                    )
                except Exception as e:
                    existed_invoice = None

                if not existed_invoice:
                    invoice = payment_models.Invoice.objects.create(
                        user=user,
                        subscription_history=subscription_history,
                        stripe_invoice_id=latest_invoice,
                        hosted_invoice_url=invoice_stripe["hosted_invoice_url"],
                    )

                MailService.send_mail_renewed_success(
                    user,
                    subscription_history.subscription_plan,
                    subscription_history,
                    invoice_stripe,
                )

            elif event["type"] == STRIPE_EVENTS["INVOICE_UPDATED"]:
                invoice_id = event["data"]["object"]["id"]
                hosted_invoice_url = event["data"]["object"]["hosted_invoice_url"]
                subscription_id = event["data"]["object"]["subscription"]

                invoice = payment_models.Invoice.objects.filter(
                    stripe_invoice_id=invoice_id
                ).first()
                if invoice:
                    invoice.hosted_invoice_url = hosted_invoice_url
                    invoice.save()

                invoice_stripe = payment_models.SubscriptionAuthUser.get_invoice(
                    invoice_id
                )

                subscription_history = (
                    payment_models.SubscriptionHistory.objects.filter(
                        stripe_subscription_id=subscription_id
                    ).first()
                )

                if subscription_history is None:
                    return JsonResponse({"status": "success"})
                
                user = payment_models.SubscriptionAuthUser.objects.filter(
                    id=subscription_history.user_id
                ).first()

                MailService.send_invoice_info(
                    user, subscription_history.subscription_plan, invoice_stripe
                )

            return JsonResponse({"status": "success"})
        except Exception as e:
            print(e)
            logger.info(e)

            return JsonResponse(
                {"error": f"Error handling event: {str(e)}"}, status=500
            )


# @celery.task
# def check_subcription_cycle():
#     today = datetime.now().date()
#     one_day_later = today + timedelta(days=1)
#     seven_day_later = today + timedelta(days=7)
#     thirty_day_later = today + timedelta(days=30)

#     one_day_list = payment_models.SubscriptionHistory.get_by_day_left(
#         payment_models.SubscriptionHistory, one_day_later
#     )
#     seven_day_list = payment_models.SubscriptionHistory.get_by_day_left(
#         payment_models.SubscriptionHistory, seven_day_later
#     )
#     thirty_day_list = payment_models.SubscriptionHistory.get_by_day_left(
#         payment_models.SubscriptionHistory, thirty_day_later
#     )

#     subscription_id_sent = ""
#     lists = list(chain(one_day_list, seven_day_list, thirty_day_list))

#     try:
#         for item in lists:
#             if item.subscription_plan.duration > 1:
#                 if item.checkout_session_link is None:
#                     data = {
#                         "subscription_plan_id": item.subscription_plan.id,
#                         "recurring_type": payment_models.SubscriptionHistory.YEARLY,
#                     }
#                     result = (
#                         payment_models.SubscriptionAuthUser.create_checkout_session(
#                             item.user.id, **data
#                         )
#                     )
#                     item.checkout_session_link = result["url"]
#                     item.save()

#                 subscription_id_sent = subscription_id_sent + " " + str(item.id)
#                 payment_models.SubscriptionAuthUser.send_req_payment_renew(
#                     item.user, item.subscription_plan, item
#                 )
#             else:
#                 payment_models.SubscriptionAuthUser.send_auto_renew_notify(
#                     item.user, item.subscription_plan, item
#                 )

#         for history in payment_models.SubscriptionHistory.objects.all():
#             if (
#                 history.start_day <= timezone.now()
#                 and history.end_day >= timezone.now()
#             ):
#                 if history.status != history.ACTIVE:
#                     history.status = history.ACTIVE
#                     history.save()

#             elif history.end_day < timezone.now() and history.status != history.EXPIRED:
#                 history.status = history.EXPIRED
#                 history.save()

#     except Exception as ex:
#         return str(ex)

#     return str(subscription_id_sent)
