from datetime import datetime

from django.conf import settings
from django.db import models


# Create your models here.
class LingoBaseModel(models.Model):
    display_name = models.CharField(verbose_name="Display Name", max_length=255)
    created_at = models.DateTimeField(
        verbose_name="Created At",
        auto_now_add=True,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Created By",
        on_delete=models.SET_NULL,
        null=True,
    )
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)

    class Meta:
        abstract = True
