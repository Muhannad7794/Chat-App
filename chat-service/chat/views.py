from rest_framework import viewsets, permissions
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        chat_room = self.get_object()
        user = request.user
        logger.debug(f"Adding member {user} to chat room {chat_room}")
        chat_room.members.add(user)
        chat_room.save()
        return Response({"status": "member added"})


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        logger.debug(f"Creating message from {sender}")
        serializer.save(sender=sender)
