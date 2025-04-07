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
        """
        Only show rooms that the current user is a member of.
        """
        return ChatRoom.objects.filter(members=self.request.user)

    #
    # 1) Enforce "admin only" for update/partial_update/destroy
    #
    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied(
                "Only the room admin can rename the room or modify its membership."
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied(
                "Only the room admin can rename the room or modify its membership."
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can delete this room.")
        return super().destroy(request, *args, **kwargs)

    #
    # 2) Optional custom actions for adding/removing members
    #    (If you want to let the admin do that via distinct endpoints)
    #
    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        """
        Admin-only action to add a user to the room.
        Expects JSON like {"username": "some_username"}
        """
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can add members.")

        username = request.data.get("username")
        if not username:
            return Response(
                {"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(username=username)
        room.members.add(user)
        room.save()
        return Response({"detail": f"User '{username}' added to the room."})

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """
        Admin-only action to remove a member from the room.
        Expects JSON like {"user_id": <int>}
        """
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can remove members.")

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_remove = room.members.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found in this room."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user_to_remove == room.admin:
            return Response(
                {"detail": "Cannot remove the admin from their own room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.members.remove(user_to_remove)
        room.save()
        return Response({"detail": f"User {user_id} removed from the room."})

    #
    # 3) A custom action to let a user leave the room on their own
    #
    @action(detail=True, methods=["post"], url_path="leave")
    def leave_room(self, request, pk=None):
        """
        Allows a non-admin user to remove themselves from the room.
        """
        room = self.get_object()
        if request.user not in room.members.all():
            return Response(
                {"detail": "You are not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If the user is the admin, we might decide they can't 'leave'
        # or that leaving would delete the room. For now, let's allow it:
        # but you can also block it if you want to force the admin to delete
        # or transfer admin privileges first.
        room.members.remove(request.user)
        room.save()
        return Response({"detail": "You have left the room."})


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
