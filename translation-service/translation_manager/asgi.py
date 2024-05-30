# transaltion_manager/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from translation.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translation_manager.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
