from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import ChatRoomViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"rooms", ChatRoomViewSet)
router.register(r"messages", MessageViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "schema/", SpectacularAPIView.as_view(), name="schema"
    ),  # OpenAPI schema endpoint
    path(
        "docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"
    ),  # Swagger-UI
]
