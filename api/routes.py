from rest_framework.routers import DefaultRouter
from django.urls import include, path

from authentication.views import UserViewSet
from text2text.views import Text2TextApi

router = DefaultRouter()

router.register("auth", UserViewSet, basename="auth")
router.register("text2text", Text2TextApi, basename="text2text")

urlpatterns = [
    path("", include(router.urls)),
]