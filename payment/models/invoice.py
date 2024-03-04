from django.db import models

from payment.models.subscription_auth_user import SubscriptionAuthUser
from payment.models.subscription_history import SubscriptionHistory
from api.models import LingoBaseModel

class Invoice(LingoBaseModel):
    CARD = "Card"
    TYPE_CHOICES = [
        (CARD, "Card"),
    ]

    user = models.ForeignKey(
        SubscriptionAuthUser,
        related_name="invoice_user",
        verbose_name="User",
        on_delete=models.CASCADE,
    )
    subscription_history = models.ForeignKey(
        SubscriptionHistory,
        related_name="invoices",
        verbose_name="Subscription Plan Line",
        on_delete=models.CASCADE,
    )
    stripe_invoice_id = models.CharField(
        verbose_name="Stripe Invoice Id", max_length=255
    )
    type = models.CharField(
        choices=TYPE_CHOICES,
        max_length=50,
        default=CARD,
        verbose_name="Invoice type name",
    )
    link_invoice_pdf = models.URLField(verbose_name="Link Invoice PDF", null=True)
    hosted_invoice_url = models.URLField(verbose_name="Hosted Invoice url", null=True)

    class Meta:
        db_table = "invoice"
        verbose_name = "Invoice"
