from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data["status_code"] = response.status_code

    return response


class AvatarRequireExcepion(APIException):
    status_code = 400
    default_detail = "Avatar image is required!"
    default_code = "avatar_required"


class RefreshTokenRequireExcepion(APIException):
    status_code = 400
    default_detail = "Refresh token is required."
    default_code = "refresh_token_required"


class EmailAndPasswordRequireExcepion(APIException):
    status_code = 400
    default_detail = "Email and password are required fields!"
    default_code = "email_password_required"


class LoginFailedExcepion(APIException):
    status_code = 401
    default_detail = "Authentication failed. Invalid email or password."
    default_code = "login_failed"


class SendEmailExcepion(APIException):
    status_code = 400
    default_detail = """Can not send an email verification to your email address!
    Please check and try again!"""
    default_code = "email_send_failed"
