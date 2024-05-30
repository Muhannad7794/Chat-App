# translation/routing.py
from django.urls import path
from .consumers import TranslationConsumer

websocket_urlpatterns = [
    path("ws/translate/<int:room_id>/", TranslationConsumer.as_asgi()),
]
