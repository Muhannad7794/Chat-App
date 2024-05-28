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
        # Ensure the user is only seeing messages from chat rooms they are part of
        user_rooms = ChatRoom.objects.filter(members=self.request.user)
        return Message.objects.filter(chat_room__in=user_rooms)

    def perform_create(self, serializer):
        # Get chat_room directly from the validated data within the serializer
        chat_room = serializer.validated_data.get("chat_room")

        # Check if the user is a member of the chat room
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")

        # Save the message with the user as the sender
        serializer.save(sender=self.request.user)
