# chat_service/chat/dispatch.py
import pika
from django.conf import settings
import json


def send_notification(message, user_id):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue="notifications")
    channel.basic_publish(
        exchange="",
        routing_key="notification",
        body=json.dumps({"user_id": user_id, "message": message}),
    )
    connection.close()
