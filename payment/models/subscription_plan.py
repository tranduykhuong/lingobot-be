from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models

from api.models import LingoBaseModel
from api.services.stripe import stripe


class SubscriptionPlan(LingoBaseModel):
    class Meta:
        db_table = "subsciption_plan"
        verbose_name = "Subscription plan"
        verbose_name_plural = "Subscription plans"
        ordering = ["name", "duration"]

    FREE = "FREE"
    PREMIUM = "PREMIUM"
    NAME_PACKAGE_CHOICES = [
        (FREE, "FREE"),
        (PREMIUM, "PREMIUM"),
    ]

    name = models.CharField(
        choices=NAME_PACKAGE_CHOICES,
        max_length=50,
        default=FREE,
        verbose_name="Subscription plan name",
    )

    is_free = models.BooleanField(default=True, verbose_name="Free account")
    price_per_plan = models.FloatField(
        validators=[MinValueValidator(0)], default=0, verbose_name="Price per plan"
    )
    duration = models.IntegerField(
        validators=[MinValueValidator(0)], default=1, verbose_name="Duration (Month)"
    )

    stripe_price_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Stripe Price ID"
    )

    is_publish = models.BooleanField(default=True, verbose_name="Is Publish?")

    def __str__(self):
        return self.name

    def create_stripe_product_and_price(self):
        if self.name == self.FREE:
            self.stripe_price_id=None
            return
        
        product = stripe.Product.create(
            name=f'{self.name} Package - {self.duration} month{"s" if self.duration != 1 else ""}',
            description=f'{self.name} Package - {self.duration} month{"s" if self.duration != 1 else ""}',
            type="service",
            active=True,
        )
        price = stripe.Price.create(
            unit_amount=int(self.price_per_plan * 100),
            currency="usd",
            recurring={
                "interval": "month",
                "interval_count": self.duration
            },
            product=product.id,
        )
        self.stripe_price_id = price.id

    def save(self, *args, **kwargs):
        try:
            old_instance = self.__class__._default_manager.get(pk=self.pk)
            if self._state.adding or self.price_per_plan != old_instance.price_per_plan:
                self.create_stripe_product_and_price()

        except ObjectDoesNotExist:
            self.create_stripe_product_and_price()

        super().save(*args, **kwargs)
