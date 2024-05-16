from django.contrib import admin
from .models import ChatRoom, Message


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_room", "sender", "content", "timestamp")
    list_filter = ("chat_room", "sender", "timestamp")
    search_fields = ("content", "sender__username", "chat_room__name")
