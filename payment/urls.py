from django.shortcuts import render
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payment.views.subscription_history_view import SubscriptionHistoryViewset
from payment.views.subscription_plan_view import SubscriptionPlanViewset
from payment.views.webhook_view import (CreateCheckoutSessionView,
                                        StripeWebhookView)

router = DefaultRouter()
router.register(
    "subscription", SubscriptionHistoryViewset, basename="subscription_history"
)
router.register(
    "subscription-plan", SubscriptionPlanViewset, basename="subscription_plan"
)

urlpatterns = [
    path(
        "create-checkout-session/",
        CreateCheckoutSessionView.as_view(),
        name="create-checkout-session",
    ),
    path("stripe-webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path(
        "payment-successful/",
        lambda request: render(request, "payment/payment_successful.html"),
    ),
    path(
        "payment-cancelled/",
        lambda request: render(request, "payment/payment_cancelled.html"),
    ),

    path("", include(router.urls)),
]
