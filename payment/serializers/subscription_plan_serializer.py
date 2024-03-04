from rest_framework import serializers

from payment.models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        exclude = ["stripe_price_id"]
