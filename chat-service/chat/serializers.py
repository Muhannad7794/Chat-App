# chat/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from .dispatch import (
    publish_chat_room_created,
    publish_new_message,
    send_notification,
    send_translation_request,
)
from .translation_handler import get_language_preference
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserNestedSerializer(serializers.ModelSerializer):
    """Serializer for returning user info (id, username)."""

    class Meta:
        model = User
        fields = ["id", "username"]


class ChatRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating ChatRoom instances.
    """

    members = UserNestedSerializer(many=True, read_only=True)
    members_usernames = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "members", "admin", "members_usernames"]
        extra_kwargs = {
            "members": {"read_only": True},
            "admin": {"read_only": True},
        }

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["admin"] = instance.admin.username
        return rep

    def create(self, validated_data):
        members_usernames = validated_data.pop("members_usernames", [])
        user = self.context["request"].user
        chat_room = ChatRoom.objects.create(**validated_data, admin=user)
        chat_room.members.add(user)
        for username in members_usernames:
            member, _ = User.objects.get_or_create(username=username)
            chat_room.members.add(member)
        chat_room.save()
        publish_chat_room_created(
            room_id=chat_room.id, room_name=chat_room.name, admin_id=chat_room.admin.id
        )
        return chat_room

    def update(self, instance, validated_data):
        if "name" in validated_data:
            instance.name = validated_data["name"]
        instance.save()
        return instance


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Message instances.
    The sender field is read-only and provided via the view's context.
    """

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender"]

    def create(self, validated_data):
        sender = self.context.get("sender")
        if not sender:
            raise serializers.ValidationError("Sender not provided in context.")
        message_instance = Message.objects.create(sender=sender, **validated_data)
        # Trigger asynchronous translation/notification events without affecting save.
        self.handle_message_translation_and_notification(message_instance)
        return message_instance

    def handle_message_translation_and_notification(self, message_instance):
        """
        Publishes a 'new message' event and for each room member triggers:
          - Translation request if the member's language preference is not "original"
          - Otherwise, a direct notification.
        """
        room_id = message_instance.chat_room.id
        sender_id = message_instance.sender.id
        content = message_instance.content

        # Publish new message event
        publish_new_message(
            message_id=message_instance.id,
            room_id=room_id,
            sender_id=sender_id,
            content=content,
        )

        # For each member, check their language preference.
        for member in message_instance.chat_room.members.all():
            lang = get_language_preference(member.id, room_id)
            # Our design: if language is "original", show as-is.
            if lang and lang != "original":
                try:
                    send_translation_request(content, lang, room_id, member.id)
                except Exception as e:
                    logger.error(
                        f"Translation request error for message {message_instance.id} for user {member.id}: {e}"
                    )
            else:
                send_notification(
                    "message",
                    {"text": content, "room": room_id, "user_id": member.id},
                )
