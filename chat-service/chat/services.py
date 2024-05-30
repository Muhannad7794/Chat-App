import pika
import json
from django.conf import settings
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
    finally:
        if connection.is_open:
            connection.close()


def send_translation_request(message, target_language, callback_queue):
    try:
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = "translation_requests"
        channel.queue_declare(queue=queue_name, durable=True)
        body = json.dumps(
            {"text": message, "lang": target_language, "callback_queue": callback_queue}
        )
        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
    finally:
        if connection.is_open:
            connection.close()
