# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model
#notifications imports
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .dispatch import send_notification

User = get_user_model()


class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name="chat_rooms")
    admin = models.ForeignKey(
        User, related_name="admin_rooms", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


@receiver(m2m_changed, sender=ChatRoom.members.through)
def notify_user_added_to_room(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            if user_id != instance.admin_id:
                send_notification(
                    "room_notifications",
                    {
                        "user_id": user_id,
                        "message": f"You have been added to a new chat room: {instance.name}",
                    },
                )
