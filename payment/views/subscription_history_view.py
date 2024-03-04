from http import HTTPStatus
from django.http import JsonResponse

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from payment import models as payment_models
from payment import serializers as payment_serializers
from api import exceptions
from api.services import stripe


class SubscriptionHistoryViewset(viewsets.ModelViewSet):
    queryset = payment_models.SubscriptionHistory.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"], url_path="history")
    def get_history_by_user(self, request, *args, **kwargs):
        instance = payment_models.SubscriptionHistory.objects.filter(
            user=request.user.id
        )

        serializer = payment_serializers.SubscriptionHistorySerializer(
            instance, many=True
        )

        return Response(data=serializer.data, status=HTTPStatus.OK)

    @action(detail=False, methods=["GET"], url_path="current-plan")
    def get_current_plan(self, request, *args, **kwargs):
        subscription = (
            payment_models.SubscriptionAuthUser.get_current_subscription_plan(
                user_id=request.user.id
            )
        )
        subscription_data = payment_serializers.SubscriptionHistorySerializer(
            subscription
        )

        return Response(data=subscription_data.data, status=HTTPStatus.OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path=r"cancel-renew/(?P<subscription_history_id>\d+)",
    )
    def cancel_auto_renew(self, request, subscription_history_id=None, *args, **kwargs):
        subscription_history = payment_models.SubscriptionHistory.objects.filter(
            id=subscription_history_id
        ).first()

        if (
            subscription_history is None
            or subscription_history.stripe_subscription_id is None
        ):
            raise exceptions.NoSubscriptionActive

        if subscription_history.user.id != request.user.id:
            raise exceptions.NotPermissionCancelSubscription

        try:
            subscription_stripe = stripe.Subscription.retrieve(
                subscription_history.stripe_subscription_id
            )

            if subscription_stripe["canceled_at"] is not None:
                return JsonResponse({"message": "Already canceled!"})

            subscription_stripe.cancel()

            subscription_history.auto_renew = False
            subscription_history.save()

        except Exception as ex:
            raise ex

        return JsonResponse({"message": "Successfully canceled auto-renewal!"})
