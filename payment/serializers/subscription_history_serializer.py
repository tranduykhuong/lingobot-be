from rest_framework import serializers

from payment.models import subscription_history
from payment.serializers.subscription_plan_serializer import \
    SubscriptionPlanSerializer


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer()

    class Meta:
        model = subscription_history.SubscriptionHistory
        fields = (
            "id",
            "user",
            "subscription_plan",
            "start_day",
            "end_day",
            "payment_status",
            "subscription_type",
            "status",
            "auto_renew",
            "created_at",
        )
