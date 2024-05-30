# chat/dispatch.py
import pika
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def get_rabbit_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST, credentials=credentials
    )
    return pika.BlockingConnection(parameters)


def send_notification(notification_type, message):
    try:
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = f"{notification_type}_notifications"
        channel.queue_declare(queue=queue_name, durable=True)
        body = json.dumps(message)
        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
        logger.debug("Message published successfully")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
    finally:
        if connection.is_open:
            connection.close()


def send_translation_request(message, target_language, user_id):
    try:
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = "translation_requests"
        channel.queue_declare(queue=queue_name, durable=True)
        body = json.dumps(
            {"text": message, "lang": target_language, "user_id": user_id}
        )
        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
        logger.debug("Translation request published successfully")
    except Exception as e:
        logger.error(f"Failed to send translation request: {e}")
    finally:
        if connection.is_open:
            connection.close()
