# chat/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .services import send_notification, send_translation_request
from .translation_handler import get_language_preference
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see rooms they are members of
        return ChatRoom.objects.filter(members=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.request.query_params.get("chat_room", None)
        if room_id is not None:
            return Message.objects.filter(
                chat_room_id=room_id, chat_room__members=self.request.user
            )
        else:
            raise PermissionDenied("Chat room not specified.")

    def perform_create(self, serializer):
        chat_room = serializer.validated_data.get("chat_room")
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")
        message_instance = serializer.save(sender=self.request.user)

        # Handle translation and notification based on member preferences
        room_members = chat_room.members.all()
        for member in room_members:
            if member.id != self.request.user.id:
                preferred_language = get_language_preference(member.id, chat_room.id)
                if preferred_language and preferred_language != "default":
                    translated_message = translate_message(
                        message_instance.content, preferred_language
                    )
                    send_notification(
                        "message",
                        {
                            "message": translated_message,
                            "room": chat_room.name,
                            "user_id": member.id,
                        },
                    )
                else:
                    send_notification(
                        "message",
                        {
                            "message": message_instance.content,
                            "room": chat_room.name,
                            "user_id": member.id,
                        },
                    )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.request.query_params.get("chat_room", None)
        if room_id is not None:
            return Message.objects.filter(
                chat_room_id=room_id, chat_room__members=self.request.user
            )
        else:
            raise PermissionDenied("Chat room not specified.")

    def perform_create(self, serializer):
        chat_room = serializer.validated_data.get("chat_room")
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")
        message = serializer.save(sender=self.request.user)
        # Notify other members in the room about the new message
        room_members = chat_room.members.exclude(id=self.request.user.id)
        for member in room_members:
            send_notification(
                "message",
                {
                    "message": f"New message from {self.request.user.username} in {chat_room.name}",
                    "room": chat_room.name,
                    "user_id": member.id,
                },
            )
