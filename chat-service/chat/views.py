# chat/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .dispatch import send_notification
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
