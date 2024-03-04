from django.db import models
from django.utils import timezone

from api.models import LingoBaseModel


class SubscriptionHistory(LingoBaseModel):
    class Meta:
        db_table = "subscription_history"
        verbose_name = "Subscription history"
        verbose_name_plural = "Subscription histories"

    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"
    SUBSCRIPTION_STATUS = [
        ("INACTIVE", "INACTIVE"),
        ("ACTIVE", "ACTIVE"),
        ("EXPIRED", "EXPIRED"),
        ("CANCELED", "CANCELED"),
    ]

    SUBSCRIPTION = "SUBSCRIPTION"
    RESUBSCRIPTION = "RESUBSCRIPTION"
    SUBSCRIPTION_TYPE = [
        ("SUBSCRIPTION", "SUBSCRIPTION"),
        ("RESUBSCRIPTION", "RESUBSCRIPTION"),
    ]

    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    PAYMENT_STATUS = [
        ("SUCCESS", "SUCCESS"),
        ("PENDING", "PENDING"),
        ("CANCELED", "CANCELED"),
    ]

    user = models.ForeignKey(
        "payment.SubscriptionAuthUser",
        related_name="subscription_histories",
        verbose_name="User",
        on_delete=models.CASCADE,
    )
    subscription_plan = models.ForeignKey(
        "payment.SubscriptionPlan", on_delete=models.PROTECT, related_name="histories"
    )
    start_day = models.DateTimeField(default=timezone.now, verbose_name="Start Day")
    end_day = models.DateTimeField(null=True, verbose_name="End Day")

    payment_status = models.CharField(
        choices=PAYMENT_STATUS,
        max_length=20,
        default=PENDING,
        verbose_name="Payment status",
    )
    subscription_type = models.CharField(
        choices=SUBSCRIPTION_TYPE,
        max_length=50,
        default=SUBSCRIPTION,
        verbose_name="Subscription Type",
    )
    status = models.CharField(
        choices=SUBSCRIPTION_STATUS,
        max_length=50,
        default=INACTIVE,
        verbose_name="Status",
    )

    auto_renew = models.BooleanField(default=False, verbose_name="Is auto renew?")
    stripe_subscription_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Stripe Subscription ID"
    )

    service_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Service data payload",
        editable=False,
    )

    def __str__(self):
        return self.subscription_plan.name

    @staticmethod
    def get_by_day_left(cls, day):
        one_list = cls.objects.filter(status=cls.ACTIVE, end_day__date=day)
        return one_list
