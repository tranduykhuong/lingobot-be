import datetime
import os

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect
from firebase_admin import storage
from rest_framework import status, viewsets
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.exceptions import (AvatarRequireExcepion,
                            EmailAndPasswordRequireExcepion,
                            LoginFailedExcepion, RefreshTokenRequireExcepion,
                            SendEmailExcepion)
from api.mixins import AuthenticationPermissionMixins
from api.utils import (ObjectResponse, StatusResponse, TokenJWT,
                       try_except_wrapper)

from .models import User
from .serializers import (UserAvatarSerializer, UserListCreateSerializer,
                          UserUpdateSerializer)

from api.mail import MailService

class UserViewSet(AuthenticationPermissionMixins, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListCreateSerializer
    lookup_field = "pk"

    @action(
        methods=["POST"],
        url_path="register",
        url_name="user-register",
        detail=False,
        permission_classes=[],
    )
    @try_except_wrapper
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        password = request.data.get("password")
        email = request.data.get("email")
        last_name = request.data.get("last_name")

        if serializer.is_valid(raise_exception=True):
            # Create Verify token
            token = TokenJWT.generate_token(serializer.validated_data)

            user = serializer.save()
            user.set_password(password)

            user.save()
            
            try:
                SERVER_ENDPOINT = os.getenv("SERVER_ENDPOINT")
                MailService.send_mail_signup_success(user=user, url_verify=f"{SERVER_ENDPOINT}/api/v1/auth/verify?token={token}")
            except Exception as e:
                print(e)

            return Response(
                ObjectResponse(
                    StatusResponse.STATUS_SUCCESS,
                    "Register account successfully.",
                    serializer.data,
                ).get_json(),
                status=status.HTTP_201_CREATED,
            )

    @action(
        methods=["POST"],
        url_path="login",
        url_name="user-login",
        detail=False,
        permission_classes=[],
    )
    @try_except_wrapper
    def login(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            raise EmailAndPasswordRequireExcepion

        user = authenticate(request, username=email, password=password)
        if user is None:
            raise LoginFailedExcepion

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        login(request, user)

        user_serializer = UserListCreateSerializer(user)

        return Response(
            ObjectResponse(
                StatusResponse.STATUS_SUCCESS,
                "Logged in successfully.",
                {
                    "user": user_serializer.data,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            ).get_json(),
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["POST"],
        url_path="logout",
        url_name="user-logout",
        detail=False,
    )
    @try_except_wrapper
    def logout(self, request):
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            return Response(
                ObjectResponse(
                    StatusResponse.STATUS_SUCCESS,
                    "Logged out successfully.",
                    "",
                ).get_json(),
                status=status.HTTP_200_OK,
            )

        raise RefreshTokenRequireExcepion

    @action(methods=["GET"], url_path="profile", detail=False)
    @try_except_wrapper
    def profile(self, request):
        user_serializer = UserListCreateSerializer(request.user)
        return Response(
            ObjectResponse(
                StatusResponse.STATUS_SUCCESS,
                "Get profile successfully.",
                user_serializer.data,
            ).get_json(),
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["GET"],
        url_path="user-profile",
        detail=False,
        permission_classes=[],
        authentication_classes=[],
    )
    @try_except_wrapper
    def get_profile_by_slug(self, request):
        slug = request.GET.get("slug")
        instance = get_object_or_404(User, slug=slug)
        user_serializer = UserListCreateSerializer(instance)
        return Response(
            ObjectResponse(
                StatusResponse.STATUS_SUCCESS,
                "Get profile successfully.",
                user_serializer.data,
            ).get_json(),
            status=status.HTTP_200_OK,
        )

    @action(methods=["PATCH"], url_path="update", detail=False)
    @try_except_wrapper
    def update_profile(self, request):
        user_serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )

        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

            return Response(
                ObjectResponse(
                    StatusResponse.STATUS_SUCCESS,
                    "Update profile successfully.",
                    user_serializer.data,
                ).get_json(),
                status=status.HTTP_200_OK,
            )

    @action(methods=["PATCH"], url_path="avatar", detail=False)
    @parser_classes([MultiPartParser, FormParser])
    @try_except_wrapper
    def update_avatar(self, request):
        avatar = request.FILES.get("avatar")

        if avatar is None:
            raise AvatarRequireExcepion

        filename = (
            str(datetime.datetime.now().timestamp())
            + "."
            + str(avatar.content_type).split("/")[1]
        )
        path = "lingobot/" + filename

        bucket = storage.bucket()
        blob = bucket.blob(path)
        blob.upload_from_string(
            avatar.read(), content_type=avatar.content_type
        )

        avatar_url = (
            "https://firebasestorage.googleapis.com/v0/b/gokag-19eac.appspot.com/o/lingobot%2F"
            + filename
            + "?alt=media"
        )

        user_serializer = UserAvatarSerializer(
            request.user, data={"avatar": avatar_url}, partial=True
        )
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

            return Response(
                ObjectResponse(
                    StatusResponse.STATUS_SUCCESS,
                    "Update avatar successfully.",
                    user_serializer.data,
                ).get_json(),
                status=status.HTTP_200_OK,
            )

    @action(
        methods=["GET"],
        url_path="verify",
        url_name="verify-email",
        detail=False,
        permission_classes=[],
    )
    @try_except_wrapper
    def verify_email(self, request):
        token = request.GET.get("token")

        try:
            data = TokenJWT.decode_token(token)

            user = get_object_or_404(User, email=data["email"])
            if user.is_verify is False:
                user.is_verify = True
                user.save()

            return redirect(os.getenv("REDIRECT_VERIFY_ENDPOINT"))
        except:
            return redirect(os.getenv("REDIRECT_VERIFY_ENDPOINT"))
