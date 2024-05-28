# chat/serializers.py
from rest_framework import serializers
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model
from .dispatch import send_notification

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
            try:
                user = User.objects.get(username=username)
                chat_room.members.add(user)
                # Send notification to each added member
                send_notification(
                    "room",
                    {
                        "message": f"You have been added to {chat_room.name}",
                        "room": chat_room.name,
                        "user_id": user.id,
                    },
                )
            except User.DoesNotExist:
                continue  # Optionally handle errors or log them
        chat_room.save()
        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["sender"]

    def create(self, validated_data):
        validated_data["sender"] = self.context[
            "request"
        ].user  # Set sender automatically
        return super().create(validated_data)
