from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .translation_handler import (
    set_language_preference,
    get_language_preference,
    translate_message,
)
from .dispatch import send_notification, send_translation_request, get_rabbit_connection
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(members=self.request.user)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def set_language(self, request):
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
