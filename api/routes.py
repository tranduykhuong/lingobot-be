from rest_framework.routers import DefaultRouter
from django.urls import include, path

from authentication.views import UserViewSet
from history.views import ParaphraseHistoryViewset
from text2text.views import Text2TextApi

router = DefaultRouter()

router.register("auth", UserViewSet, basename="auth")
router.register("paraphrase-history", ParaphraseHistoryViewset, basename="paraphrase-history")
router.register("text2text", Text2TextApi, basename="text2text")

urlpatterns = [
    path("payment/", include("payment.urls")),
    path("", include(router.urls)),
]