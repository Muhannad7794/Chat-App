# chat_service/chat/dispatch.py
import pika
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def send_notification(message, user_id):
    try:
        logger.debug("Connecting to RabbitMQ")
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST, credentials=credentials
            )
        )
        channel = connection.channel()

        queue_name = "notifications"
        logger.debug(f"Declaring queue {queue_name}")
        channel.queue_declare(queue=queue_name)

        body = json.dumps({"user_id": user_id, "message": message})
        logger.debug(f"Publishing message: {body}")
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=body,
        )
        logger.debug("Message published successfully")

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
    finally:
        if connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection closed")
