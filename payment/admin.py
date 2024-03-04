from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, mark_safe

from payment.models import Invoice, SubscriptionHistory, SubscriptionPlan


class SubscriptionHistoryAdmin(admin.ModelAdmin):
    model = SubscriptionHistory

    list_display = (
        "id",
        "subscription_plan",
        "user",
        "start_day",
        "end_day",
        "status",
        "payment__status",
        "view_invoice",
    )
    search_fields = [
        "id",
        "user__email"
    ]
    list_filter = [
        "payment_status",
        "status"
    ]

    exclude = (
        "display_name",
        "created_by",
        "auto_renew",
        "stripe_subscription_id",
        "subscription_type",
    )
    readonly_fields = ("view_invoice",)

    @admin.display(description="Payment Status")
    def payment__status(self, obj):
        if obj.subscription_plan.name == "FREE":
            return "None"

        return obj.payment_status

    def view_invoice(self, obj):
        invoices = Invoice.objects.filter(subscription_history=obj)
        if invoices:
            invoice_links = [
                f'<a href="{invoice.hosted_invoice_url}" target="_blank">Invoice</a>'
                for index, invoice in enumerate(invoices)
            ]
            return mark_safe("<br>".join(invoice_links))
        return "No invoices available"

    view_invoice.short_description = "Invoice"


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"

    def clean_duration(self):
        duration = self.cleaned_data["duration"]
        if duration <= 0:
            raise forms.ValidationError("Duration must be a positive number.")
        return duration


class SubscriptionPlanAdmin(admin.ModelAdmin):
    form = SubscriptionPlanForm
    list_display = [
        "id",
        "name",
        "is_free",
        "duration",
        "view_button"
    ]
    list_filter = [
        "name",
        "duration",
    ]
    sortable_by = (
        "id",
        "name",
        "duration",
    )

    exclude = ["stripe_price_id"]

    def view_button(self, obj):
        return format_html(
            '<a class="view-button" href="{}">View</a></br>',
            reverse("admin:payment_subscriptionplan_change", args=[obj.id]),
        )

    view_button.short_description = "Action"


# Register your models here.
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(SubscriptionHistory, SubscriptionHistoryAdmin)
