# translation/urls.py

from django.urls import path
from .views import TranslationAPIView, TranslationResultAPIView

urlpatterns = [
    path("translate/", TranslationAPIView.as_view(), name="translate"),
    path(
        "result/<str:correlation_id>/",
        TranslationResultAPIView.as_view(),
        name="translation_result",
    ),
]
