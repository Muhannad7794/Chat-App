# transaltion_manager/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore
from channels.auth import AuthMiddlewareStack  # type: ignore
from django.core.asgi import get_asgi_application
from translation.routing import websocket_urlpatterns  # type: ignore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translation_manager.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
