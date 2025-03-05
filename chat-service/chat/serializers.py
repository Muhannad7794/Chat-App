from rest_framework import serializers
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model
from .dispatch import send_notification, send_translation_request
from .translation_handler import get_language_preference

User = get_user_model()


class ChatRoomSerializer(serializers.ModelSerializer):
    members_usernames = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = ChatRoom
        fields = ["id", "name", "members", "admin", "members_usernames"]
        extra_kwargs = {"members": {"read_only": True}, "admin": {"read_only": True}}

    def create(self, validated_data):
        members_usernames = validated_data.pop("members_usernames", [])
        chat_room = ChatRoom.objects.create(
            **validated_data, admin=self.context["request"].user
        )
        chat_room.members.add(self.context["request"].user)
        for username in members_usernames:
            user, _ = User.objects.get_or_create(username=username)
            chat_room.members.add(user)
            send_notification(
                "room",
                {
                    "message": f"You have been added to {chat_room.name}",
                    "room": chat_room.name,
                    "user_id": user.id,
                },
            )
        chat_room.save()
        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender"]

    def create(self, validated_data):
        message_instance = super().create(validated_data)
        self.handle_message_translation_and_notification(message_instance)
        return message_instance

    def handle_message_translation_and_notification(self, message_instance):
        room_id = message_instance.chat_room.id
        sender_id = message_instance.sender.id
        content = message_instance.content

        # Fetch language preferences for all members in the room
        members = message_instance.chat_room.members.all()
        for member in members:
            lang = get_language_preference(member.id, room_id)
            if lang and lang != "default":
                send_translation_request(content, lang, room_id, member.id)
            else:
                send_notification(
                    "message", {"text": content, "room": room_id, "user_id": member.id}
                )
