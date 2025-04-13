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
        return ChatRoom.objects.filter(members=self.request.user)

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.admin != request.user:
            raise PermissionDenied("Only the room admin can rename or modify the room.")
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
            raise PermissionDenied("Only the room admin can modify this room.")
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
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.request.query_params.get("chat_room")
        if not room_id:
            raise PermissionDenied("Chat room not specified.")
        # Adding distinct() and ordering to avoid duplicate rows.
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
        return context

    def perform_create(self, serializer):
        chat_room = serializer.validated_data.get("chat_room")
        if self.request.user not in chat_room.members.all():
            raise PermissionDenied("You are not a member of this room.")
        # Save the message using the sender passed in context.
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
                                message_instance.id,
                            )
                        except Exception as e:
                            logger.error(
                                f"Translation request failed for msg {message_instance.id} for user {member.id}: {e}"
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
