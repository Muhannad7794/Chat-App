# chat-sevice/chat/translation_handler.py
import json
import requests
from django.conf import settings
import pika
import logging
import redis
from django.core.cache import cache

logger = logging.getLogger(__name__)

language_preferences = {}


def get_language_preference(user_id, room_id):
    return language_preferences.get((user_id, room_id), "default")


def set_language_preference(user_id, room_id, language_code):
    language_preferences[(user_id, room_id)] = language_code
    logger.debug(
        f"Set language preference for user {user_id} in room {room_id} to {language_code}"
    )
    send_language_change_notification(user_id, room_id, language_code)


def translate_message(message, target_language):
    """Send a translation request to Azure Translation API."""
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }
    body = [{"text": message}]
    endpoint = f"{settings.AZURE_TRANSLATOR_ENDPOINT}/translate?api-version=3.0&to={target_language}"
    response = requests.post(endpoint, headers=headers, json=body)
    if response.status_code == 200:
        translated_text = response.json()[0]["translations"][0]["text"]
        return translated_text
    else:
        return message  # Fallback to the original message if translation fails


def get_rabbit_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST, credentials=credentials
    )
    return pika.BlockingConnection(parameters)


def send_language_change_notification(user_id, room_id, language_code):
    connection = None
    try:
        connection = get_rabbit_connection()
        channel = connection.channel()
        queue_name = "language_change_notifications"
        channel.queue_declare(queue=queue_name, durable=True)
        message = {
            "user_id": user_id,
            "room_id": room_id,
            "language_code": language_code,
        }
        body = json.dumps(message)
        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
        logger.debug(f"Published language change notification: {body}")
    except Exception as e:
        logger.error(f"Failed to send language change notification: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
