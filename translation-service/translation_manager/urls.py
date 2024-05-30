# translation_manager/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # include the urls from the translation app
    path("translation/", include("translation.urls")),
]
