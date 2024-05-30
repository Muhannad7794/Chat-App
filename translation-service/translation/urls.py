# translation/urls.py
from django.urls import path
from .views import handle_translation_request

urlpatterns = [
    path("translate/", handle_translation_request, name="translate"),
]
