#chat_manager/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", include("chat.urls")),  # Including the chat app URLs
]
