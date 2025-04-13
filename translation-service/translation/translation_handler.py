# translation/translation_handler.py

import json
import requests
import uuid
import logging
from django.conf import settings
from django.core.cache import cache
import pika  # type: ignore

logger = logging.getLogger(__name__)

# Define the default value meaning "do not translate"
DEFAULT_LANGUAGE = "original"


def get_language_preference(user_id, room_id):
    """
    Retrieves the language preference from Redis (via Django cache) for a given user and room.
    If not set, returns DEFAULT_LANGUAGE.
    """
    key = f"user_{user_id}_room_{room_id}_lang"
    lang = cache.get(key)
    return lang if lang is not None else DEFAULT_LANGUAGE


def set_language_preference(user_id, room_id, language_code):
    """
    Sets the language preference for a given user and room using Django cache (Redis).
    """
    key = f"user_{user_id}_room_{room_id}_lang"
    cache.set(
        key, language_code, timeout=None
    )  # Persist indefinitely (or adjust timeout as needed)
    logger.debug(
        f"Set language preference for user {user_id} in room {room_id} to {language_code}"
    )
    send_language_change_notification(user_id, room_id, language_code)


def translate_message(message, target_language):
    """
    Calls the Azure Translator API synchronously.
    Returns the translated text; if an error occurs, returns the original message.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }
    body = [{"text": message}]
    endpoint = f"{settings.AZURE_TRANSLATOR_ENDPOINT.rstrip('/')}/translate?api-version=3.0&to={target_language}"
    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        if response.status_code == 200:
            translated_text = response.json()[0]["translations"][0]["text"]
            return translated_text
        else:
            logger.error(
                f"Azure Translator error {response.status_code}: {response.text}"
            )
            return message
    except Exception as e:
        logger.error(f"Error calling Azure Translator API: {e}")
        return message


def get_rabbit_connection():
    """
    Establishes a connection to RabbitMQ using settings.
    """
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


def send_language_change_notification(user_id, room_id, language_code):
    """
    Publishes a language-change notification to a dedicated RabbitMQ queue.
    """
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
