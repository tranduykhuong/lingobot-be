from django.core.mail import send_mail
from django.template.loader import render_to_string

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
