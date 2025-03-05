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
    connection = None
    try:
        logger.debug("Connecting to RabbitMQ")
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = f"{notification_type}_notifications"
        logger.debug(f"Declaring queue {queue_name}")
        channel.queue_declare(queue=queue_name, durable=True)
        body = json.dumps(message)
        logger.debug(f"Publishing message: {body}")
        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
        logger.debug("Message published successfully")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection closed")


def send_translation_request(text, target_language, room_id, user_id):
    connection = None
    try:
        logger.debug("Connecting to RabbitMQ for translation request")
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = "translation_request_queue"
        logger.debug(f"Declaring queue {queue_name}")
        channel.queue_declare(queue=queue_name, durable=True)
        message = json.dumps(
            {
                "text": text,
                "lang": target_language,
                "room_id": room_id,
                "user_id": user_id,
            }
        )
        logger.debug(f"Publishing translation request: {message}")
        channel.basic_publish(exchange="", routing_key=queue_name, body=message)
        logger.debug("Translation request published successfully")
    except Exception as e:
        logger.error(f"Failed to send translation request: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection closed")
