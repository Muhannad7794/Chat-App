# users_management/users/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .rabbitmq import send_notification

User = get_user_model()


@receiver(post_save, sender=User)
def notify_new_user_registration(sender, instance, created, **kwargs):
    if created:
        message = {
            "type": "new_user",
            "message": f"New user registered: {instance.username}",
        }
        send_notification("registration_notifications", message)
