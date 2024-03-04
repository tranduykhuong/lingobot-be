from datetime import datetime, timedelta

from django.conf import settings
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

from authentication.models import User
from payment import models as payment_models
from api import exceptions
from api.services.stripe import stripe


class SubscriptionAuthUser(User):
    class Meta:
        proxy = True

    def __str__(self):
        return self.email

    @staticmethod
    def create_checkout_session(user_id, **data):
        subscription_plan = payment_models.SubscriptionPlan.objects.get(
            id=data["subscription_plan_id"]
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=user_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": subscription_plan.stripe_price_id,
                        "quantity": 1,
                    },
                ],
                success_url=settings.STRIPE_REDIRECT_SUCCESS_URL,
                cancel_url=settings.STRIPE_REDIRECT_CANCEL_URL,
                metadata={
                    "price_id": subscription_plan.stripe_price_id,
                },
                mode="subscription",
            )
            return {"session_id": checkout_session.id, "url": checkout_session.url}
        except Exception as e:
            print(f"Create checkout session error, reason: {e}")

    @staticmethod
    def get_invoice(invoice_id):
        return stripe.Invoice.retrieve(invoice_id)

    @staticmethod
    def get_price_id(subscription_id):
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription["items"]["data"][0]["price"]["id"]


    @classmethod
    def get_current_subscription_plan(self, user_id):
        instance = self.objects.get(id=user_id)
        subscription_histories = instance.subscription_histories.all()
        subscription_history_free = None

        for history in subscription_histories:
            if history.subscription_plan.name == payment_models.SubscriptionPlan.FREE:
                subscription_history_free = history
            elif history.status == history.CANCELED:
                continue
            elif (
                history.start_day <= timezone.now()
                and history.end_day >= timezone.now()
            ):
                if history.status != history.ACTIVE:
                    history.status = history.ACTIVE
                    history.save()
                return history
            elif history.end_day < timezone.now() and history.status != history.EXPIRED:
                history.status = history.EXPIRED
                history.save()

        if subscription_history_free is None:
            try:
                subscription_plan_free = payment_models.SubscriptionPlan.objects.filter(
                    name=payment_models.SubscriptionPlan.FREE
                ).first()
                subscription_history_free = payment_models.SubscriptionHistory.objects.create(
                    user=instance,
                    subscription_plan=subscription_plan_free,
                    start_day=datetime.now(),
                    end_day=datetime.now() + timedelta(days=5 * 365),
                    payment_status=payment_models.SubscriptionHistory.SUCCESS,
                    subscription_type=payment_models.SubscriptionHistory.SUBSCRIPTION,
                    status=payment_models.SubscriptionHistory.ACTIVE,
                )
            except Exception as e:
                raise exceptions.NoSubscriptionActive

        return subscription_history_free
