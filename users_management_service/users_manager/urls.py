from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, LoginView  # Adjust the import path as necessary
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"users", UserViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(router.urls)),
    path("login/", LoginView.as_view(), name="login"),
    # Schema and Swagger UI
    path("/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Include other application URLs as needed
]
