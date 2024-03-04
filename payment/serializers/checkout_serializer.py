from rest_framework import serializers

from payment.models.subscription_history import SubscriptionHistory


class CheckoutDeserializer(serializers.Serializer):
    subscription_plan_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1)


class CheckoutSerializer(serializers.Serializer):
    session_id = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
