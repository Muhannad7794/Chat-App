# translation/routing.py
from django.urls import path
from translation.consumers import TranslationConsumer

websocket_urlpatterns = [
    path("ws/translate/", TranslationConsumer.as_asgi()),
]
