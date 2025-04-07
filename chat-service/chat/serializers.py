# chat/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import ChatRoom, Message
from .dispatch import (
    publish_chat_room_created,
    publish_new_message,
    send_notification,  # Kept for user-level notifications
    send_translation_request,  # Kept for translation queue
)
from .translation_handler import get_language_preference

User = get_user_model()


class UserNestedSerializer(serializers.ModelSerializer):
    """Simple serializer for returning user info (id, username)."""

    class Meta:
        model = User
        fields = ["id", "username"]


class ChatRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating ChatRoom instances.
    """

    # We'll replace the default `members` with a nested serializer
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
        ret = super().to_representation(instance)
        # Replace the admin field with the admin's username
        ret["admin"] = instance.admin.username
        return ret

    def update(self, instance, validated_data):
        """
        Allows the room name to be updated if provided.
        Ignores members here because we handle that
        in the view's custom actions for add/remove.
        """
        if "name" in validated_data:
            instance.name = validated_data["name"]
        instance.save()
        return instance

    def create(self, validated_data):
        members_usernames = validated_data.pop("members_usernames", [])
        chat_room = ChatRoom.objects.create(
            **validated_data, admin=self.context["request"].user
        )
        # Always add the creator as a member
        chat_room.members.add(self.context["request"].user)

        # Add each user from 'members_usernames'
        for username in members_usernames:
            user, _ = User.objects.get_or_create(username=username)
            chat_room.members.add(user)

        chat_room.save()

        # Publish the "chat room created" event
        publish_chat_room_created(
            room_id=chat_room.id, room_name=chat_room.name, admin_id=chat_room.admin.id
        )

        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Message instances.
    """

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender"]

    def create(self, validated_data):
        """
        Creates a new message, then handles translation & notification logic.
        """
        message_instance = super().create(validated_data)
        self.handle_message_translation_and_notification(message_instance)
        return message_instance

    def handle_message_translation_and_notification(self, message_instance):
        """
        1) Publishes a 'new message' event to RabbitMQ.
        2) For each member in the chat room, either send a translation request
           or a user-level notification (if language == 'default').
        """
        room_id = message_instance.chat_room.id
        sender_id = message_instance.sender.id
        content = message_instance.content

        # 1) Publish a "new message" event for global consumption
        publish_new_message(
            message_id=message_instance.id,
            room_id=room_id,
            sender_id=sender_id,
            content=content,
        )

        # 2) User-specific logic (translation requests or notifications)
        members = message_instance.chat_room.members.all()
        for member in members:
            lang = get_language_preference(member.id, room_id)
            if lang and lang != "default":
                # Queue a translation request
                send_translation_request(content, lang, room_id, member.id)
            else:
                # Send a direct notification (if still desired)
                send_notification(
                    "message",
                    {"text": content, "room": room_id, "user_id": member.id},
                )
