from datetime import datetime
from django.utils import timezone

from django.core.mail import send_mail
from django.template.loader import render_to_string

from payment import models as payment_models

class MailService:
    @staticmethod
    def send_mail_signup_success(user, url_verify):
        send_mail(
            "REGISTER ACCOUNT SUCCESSFULLY",
            message="",
            html_message=render_to_string(
                "../templates/email/signup_success.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "url_verify": url_verify
                },
            ),
            from_email="noreply@lingobot.com",
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_mail_subscription_success(
        user, subscription_plan, subscription_history, invoice_stripe
    ):
        send_mail(
            "SUCCESSFULLY SUBSCRIPTION",
            message="",
            html_message=render_to_string(
                "../templates/email/subscription_success.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "package_name": subscription_plan.name,
                    "package_duration": int(subscription_plan.duration),
                    "package_start": subscription_history.start_day,
                    "package_end": subscription_history.end_day,
                    "invoice_number": invoice_stripe["number"] if invoice_stripe is not None else None,
                    "payment_date": datetime.utcfromtimestamp(
                        invoice_stripe["created"]
                    ).strftime("%b. %d, %Y, %-I:%M %p") if invoice_stripe is not None else timezone.now(),
                    "total_price": invoice_stripe["total"] / 100 if invoice_stripe is not None else subscription_plan.price_per_plan,
                    "link_to_invoice": invoice_stripe["hosted_invoice_url"] if invoice_stripe is not None else None,
                    "auto_renew": subscription_history.auto_renew,
                },
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_mail_renewed_success(
        user, subscription_plan, subscription_history, invoice_stripe
    ):
        send_mail(
            "SUCCESSFULLY RENEWED",
            message="",
            html_message=render_to_string(
                "../templates/email/renew_success.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "package_name": subscription_plan.name,
                    "package_duration": int(subscription_plan.duration),
                    "package_start": subscription_history.start_day,
                    "package_end": subscription_history.end_day,
                    "invoice_number": invoice_stripe["number"] if invoice_stripe is not None else None,
                    "payment_date": datetime.utcfromtimestamp(
                        invoice_stripe["created"]
                    ).strftime("%b. %d, %Y, %-I:%M %p") if invoice_stripe is not None else timezone.now(),
                    "total_price": invoice_stripe["total"] / 100 if invoice_stripe is not None else subscription_plan.price_per_plan,
                    "link_to_invoice": invoice_stripe["hosted_invoice_url"] if invoice_stripe is not None else None,
                    "auto_renew": subscription_history.auto_renew,
                },
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_invoice_info(user, subscription_plan, invoice_stripe):
        send_mail(
            "INVOICE INFORMATION",
            message="",
            html_message=render_to_string(
                "../templates/email/invoice_info.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "package_name": subscription_plan.name,
                    "invoice_number": invoice_stripe["number"],
                    "payment_date": datetime.utcfromtimestamp(
                        invoice_stripe["created"]
                    ).strftime("%b. %d, %Y, %-I:%M %p"),
                    "total_price": invoice_stripe["total"] / 100,
                    "link_to_invoice": invoice_stripe["hosted_invoice_url"],
                },
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_req_payment_renew(user, subscription_plan, subscription_history):
        end_date = subscription_history.end_day.date()
        current_date = datetime.now().date()

        delta = end_date - current_date

        send_mail(
            "SUBSCRIPTION PAYMENT",
            message="",
            html_message=render_to_string(
                "../templates/email/req_payment_notify.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "package_name": subscription_plan.name,
                    "package_duration": int(subscription_plan.duration),
                    "package_start": subscription_history.start_day,
                    "package_end": subscription_history.end_day,
                    "checkout_session_link": subscription_history.checkout_session_link,
                    "day_left": delta.days,
                },
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def send_auto_renew_notify(user, subscription_plan, subscription_history):
        end_date = subscription_history.end_day.date()
        current_date = datetime.now().date()

        delta = end_date - current_date

        if (
            delta.days == 30
            and subscription_history.recurring_type
            == payment_models.SubscriptionHistory.MONTHLY
        ):
            return

        send_mail(
            "RENEW SUBSCRIPTION",
            message="",
            html_message=render_to_string(
                "../templates/email/auto_renew_notify.html",
                {
                    "recipient_name": f'{user.first_name} {user.last_name}',
                    "package_name": subscription_plan.name,
                    "package_duration": int(subscription_plan.duration),
                    "package_start": subscription_history.start_day,
                    "package_end": subscription_history.end_day,
                    "day_left": delta.days,
                },
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
