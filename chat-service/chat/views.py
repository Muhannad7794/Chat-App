# chat/views.py

from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .translation_handler import set_language_preference
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show rooms that the current user is a member of
        return ChatRoom.objects.filter(members=self.request.user)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def set_language(self, request):
        """
        Allows a user to set a preferred language for a specific chat room.
        """
        chat_room_id = request.data.get("chat_room")
        language = request.data.get("language")
        if not chat_room_id or not language:
            return Response(
                {"detail": "Chat room and language are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat_room = ChatRoom.objects.filter(
            id=chat_room_id, members=request.user
        ).first()
        if not chat_room:
            raise PermissionDenied("You are not a member of this room.")

        set_language_preference(request.user.id, chat_room.id, language)
        return Response({"detail": "Language preference set successfully."})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, and deleting messages.
    Creation logic is delegated to the serializer, which handles
    translation requests and RabbitMQ notifications.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ensures a user can only view messages in rooms they belong to.
        """
        room_id = self.request.query_params.get("chat_room")
        if not room_id:
            raise PermissionDenied("Chat room not specified.")
        return Message.objects.filter(
            chat_room_id=room_id, chat_room__members=self.request.user
        )

    def perform_create(self, serializer):
        """
        Validates that the user is a member of the chat room,
        then saves the message. The serializer handles translation
        and notification logic (see MessageSerializer).
        """
        chat_room = serializer.validated_data.get("chat_room")
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")

        # The serializer's create() method will handle:
        # - publish_new_message (RabbitMQ)
        # - send_translation_request or send_notification (per user language)
        serializer.save(sender=self.request.user)
