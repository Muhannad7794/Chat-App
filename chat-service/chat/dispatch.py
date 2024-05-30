import pika
from django.conf import settings
import json
import logging
from .services import send_notification, send_translation_request

logger = logging.getLogger(__name__)


def get_rabbit_connection():
    """Helper function to create a RabbitMQ connection."""
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST, credentials=credentials
    )
    return pika.BlockingConnection(parameters)


def send_notification(notification_type, message):
    """Send notifications to specific RabbitMQ queue."""
    try:
        logger.debug("Connecting to RabbitMQ")
        connection = get_rabbit_connection()
        channel = connection.channel()

        queue_name = f"{notification_type}_notifications"
        logger.debug(f"Declaring queue {queue_name}")
        channel.queue_declare(queue=queue_name, durable=True)

        body = json.dumps(message)
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
        if connection and connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection closed")


def send_translation_request(message, target_language, callback_queue):
    """Send a translation request to the translation service via RabbitMQ, now using translation_handler."""
    try:
        logger.debug("Connecting to RabbitMQ for translation request")
        connection = get_rabbit_connection()
        channel = connection.channel()

        translated_message = translate_message(
            message, target_language
        )  # Utilize the centralized translation logic

        queue_name = "translation_responses"  # Queue to handle translated messages
        channel.queue_declare(queue=queue_name, durable=True)

        body = json.dumps(
            {
                "text": translated_message,  # Use translated message
                "callback_queue": callback_queue,
            }
        )
        logger.debug(f"Publishing translation response: {body}")
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=body,
        )
        logger.debug("Translation response published successfully")

    except Exception as e:
        logger.error(f"Failed to send translation response: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection for translation response closed")
