from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/", include("users.urls")
    ),  # This includes the users app urls under the /api/ path
]
