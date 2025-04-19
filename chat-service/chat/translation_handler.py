# chat-sevice/chat/translation_handler.py
import json
import requests
from django.conf import settings
import pika  # type: ignore
import logging
import redis  # type: ignore
from django.core.cache import cache

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "original"


def get_language_preference(user_id, room_id):
    key = f"user_{user_id}_room_{room_id}_lang"
    lang = cache.get(key)
    return lang if lang is not None else DEFAULT_LANGUAGE


def set_language_preference(user_id, room_id, language_code):
    key = f"user_{user_id}_room_{room_id}_lang"
    cache.set(key, language_code, timeout=None)
    logger.debug(
        f"Set language preference for user {user_id} in room {room_id} to {language_code}"
    )
    send_language_change_notification(user_id, room_id, language_code)


def get_rabbit_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host="rabbitmq", port=5672, credentials=credentials
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
