from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomAuthToken, Logout, ValidateTokenView, UserInfoView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "verify/<uuid:verification_code>/",
        UserViewSet.as_view({"get": "verify_email"}),
        name="user-verify",
    ),
    path("api-token-auth/", CustomAuthToken.as_view(), name="api-token-auth"),
    path("validate-token/", ValidateTokenView.as_view(), name="validate-token"),
    path("logout/", Logout.as_view(), name="logout"),
    path("user-info/", UserInfoView.as_view(), name="user-info"),
]
