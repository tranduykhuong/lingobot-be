from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models

from api.models import LingoBaseModel
from api.services.stripe import stripe


class ParaphraseHistory(LingoBaseModel):
    class Meta:
        db_table = "paraphrase_history"
        verbose_name = "Paraphrase history"
        verbose_name_plural = "Paraphrase histories"

    user = models.ForeignKey(
        "authentication.User",
        related_name="paraphrase_histories",
        verbose_name="User",
        on_delete=models.CASCADE,
    )

    input = models.CharField(max_length=26000)
    output = models.JSONField(
        null=True,
        blank=True,
    )

    model_type = models.CharField(max_length=128)
    text_style = models.CharField(max_length=128)

    def __str__(self):
        return self.input
