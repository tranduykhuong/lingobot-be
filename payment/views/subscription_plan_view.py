from http import HTTPStatus
from itertools import groupby

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from payment import models as payment_models
from payment import serializers as payment_serializers


class SubscriptionPlanViewset(viewsets.ModelViewSet):
    queryset = payment_models.SubscriptionPlan.objects.all()
    serializer_class = payment_serializers.SubscriptionPlanSerializer

    @action(detail=False, methods=["GET"], url_path="plan")
    def get_subscription_plan(self, request, *args, **kwargs):
        queryset = payment_models.SubscriptionPlan.objects.filter(
            is_publish=True
        ).order_by("name")
        serializer = self.serializer_class(queryset, many=True)

        grouped_data = {}
        for key, group in groupby(serializer.data, key=lambda x: x["name"]):
            grouped_data[key] = sorted(list(group), key=lambda x: x["duration"])

        return Response(data=grouped_data, status=HTTPStatus.OK)
