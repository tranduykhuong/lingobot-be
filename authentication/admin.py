from .models import User
from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class AuthUserAdmin(admin.ModelAdmin):
    model = User

    fields = (
        "email",
        "first_name",
        "last_name",
        "password",
    )
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "is_verify",
        "is_active",
    )
    search_fields = [
        "first_name",
        "last_name",
        "email",
    ]

admin.site.register(User, AuthUserAdmin)
admin.site.unregister(Group)
admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
