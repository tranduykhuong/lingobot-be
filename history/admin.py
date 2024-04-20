from typing import Any
from django import forms
from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest

from history.models import ParaphraseHistory


class ParaphraseHistoryAdmin(admin.ModelAdmin):
    model = ParaphraseHistory

    list_display = (
        "id",
        "user",
        "model_type",
        "text_style",
        "input",
        "output",
        "created_at",
    )
    search_fields = [
        "id",
        "user__email"
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False

admin.site.register(ParaphraseHistory, ParaphraseHistoryAdmin)

