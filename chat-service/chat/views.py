# chat/views.py

from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .translation_handler import set_language_preference, get_language_preference
from .dispatch import (
    publish_chat_room_deleted,
    publish_chat_room_renamed,
    publish_member_removed,
    publish_member_left,
    send_notification,
    send_translation_request,
    publish_user_invited,
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Only show rooms where the current user is a member.
        """
        return ChatRoom.objects.filter(members=self.request.user)

    @action(detail=False, methods=["post"], url_path="set-language")
    def set_language(self, request):
        """
        Endpoint to set language preference.
        Expects JSON: { "chat_room": <room_id>, "language": <lang_code> }
        A value of "original" means no translation (use the message as sent).
        """
        room_id = request.data.get("chat_room")
        language = request.data.get("language")
        if not room_id or language is None:
            return Response(
                {"detail": "chat_room and language are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Verify that the user is a member of the chat room.
        from .models import ChatRoom

        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .translation_handler import set_language_preference

        set_language_preference(request.user.id, room.id, language)
        return Response(
            {"detail": f"Language set to {language}."}, status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied(
                "Only the room admin can rename the room or modify its membership."
            )
        old_name = room.name
        response = super().update(request, *args, **kwargs)
        new_name = response.data.get("name")
        if old_name != new_name:
            publish_chat_room_renamed(room.id, old_name, new_name)
            for member in room.members.all():
                if member != room.admin:
                    send_notification(
                        "room_renamed",
                        {
                            "room_id": room.id,
                            "old_name": old_name,
                            "new_name": new_name,
                            "user_id": member.id,
                        },
                    )
        return response

    def partial_update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can modify the room.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can delete this room.")
        room_id = room.id
        member_ids = [
            member.id for member in room.members.all() if member != room.admin
        ]
        response = super().destroy(request, *args, **kwargs)
        publish_chat_room_deleted(room_id)
        for member_id in member_ids:
            send_notification(
                "room_deleted", {"room_id": room_id, "user_id": member_id}
            )
        return response

    @action(detail=True, methods=["post"], url_path="add-member")
    def add_member(self, request, pk=None):
        """
        Admin-only action to add a user. Expects JSON: {"username": "some_username"}.
        """
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can add members.")
        username = request.data.get("username")
        if not username:
            return Response(
                {"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        user, _ = User.objects.get_or_create(username=username)
        room.members.add(user)
        room.save()
        publish_user_invited(user.id, room.id, room.name)
        return Response({"detail": f"User '{username}' added to the room."})

    @action(detail=True, methods=["post"], url_path="remove-member")
    def remove_member(self, request, pk=None):
        """
        Admin-only action to remove a user. Expects JSON: {"user_id": <int>}.
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
                {"detail": "Cannot remove the admin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        room.members.remove(user_to_remove)
        room.save()
        publish_member_removed(room.id, user_to_remove.id)
        return Response({"detail": f"User {user_id} removed from the room."})

    @action(detail=True, methods=["post"], url_path="leave")
    def leave_room(self, request, pk=None):
        """
        Allows a non-admin user to leave the room.
        """
        room = self.get_object()
        if request.user not in room.members.all():
            return Response(
                {"detail": "You are not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if room.admin == request.user:
            return Response(
                {"detail": "Admin cannot leave the room."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        room.members.remove(request.user)
        room.save()
        publish_member_left(room.id, request.user.id)
        return Response({"detail": "You have left the room."})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, and deleting messages.
    The serializer's create() method attaches the sender from context.
    After saving, asynchronous translation events are triggered.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.request.query_params.get("chat_room")
        if not room_id:
            raise PermissionDenied("Chat room not specified.")
        # Use distinct() and order_by to avoid duplicates.
        return (
            Message.objects.filter(
                chat_room_id=room_id, chat_room__members=self.request.user
            )
            .distinct()
            .order_by("timestamp")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["sender"] = self.request.user
        context["request"] = self.request  # ✅ Add this line
        return context

    def perform_create(self, serializer):
        chat_room = serializer.validated_data.get("chat_room")
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")
        # Save the message with the sender provided in the context.
        message_instance = serializer.save()

        # Define a function to trigger translation events and notifications.
        def publish_translation_events():
            for member in chat_room.members.all():
                if member != self.request.user:
                    target_language = get_language_preference(member.id, chat_room.id)
                    # If a language preference other than "original" is set, then fire a translation request.
                    if target_language and target_language != "original":
                        try:
                            send_translation_request(
                                message_instance.content,
                                target_language,
                                chat_room.id,
                                member.id,
                            )
                        except Exception as e:
                            logger.error(
                                f"Error sending translation request for message {message_instance.id} for user {member.id}: {e}"
                            )
                    else:
                        send_notification(
                            "message",
                            {
                                "text": message_instance.content,
                                "room": chat_room.id,
                                "user_id": member.id,
                            },
                        )

        transaction.on_commit(publish_translation_events)
