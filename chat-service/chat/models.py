# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

# Import the new publisher function from dispatch.py
from .dispatch import publish_user_invited

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
    """
    Signal receiver that fires whenever members are added to a ChatRoom.
    When new users are added (post_add), publish an event to RabbitMQ
    indicating the user was invited to the room.
    """
    if action == "post_add":
        for user_id in pk_set:
            # Avoid notifying the room admin about being added to their own room
            if user_id != instance.admin_id:
                publish_user_invited(
                    user_id=user_id, room_id=instance.id, room_name=instance.name
                )
