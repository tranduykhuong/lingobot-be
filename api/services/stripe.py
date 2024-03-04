import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY_TEST


STRIPE_EVENTS = {
    "CHECKOUT_SESSION_COMPLETED": "checkout.session.completed",
    "CUSTOMER_SUBSCRIPTION_UPDATE": "customer.subscription.updated",
    "INVOICE_UPDATED": "invoice.updated",
}