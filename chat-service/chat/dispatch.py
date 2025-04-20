# chat-service/chat/dispatch.py
import pika  # type: ignore
from django.conf import settings
import json
import logging
import uuid

logger = logging.getLogger(__name__)

# queue names:
CHAT_ROOM_CREATED_QUEUE = "chat_room_created_queue"
USER_INVITED_QUEUE = "user_invited_queue"
NEW_MESSAGE_QUEUE = "new_message_queue"
MESSAGE_PROCESSED_QUEUE = "message_processed_queue"
CHAT_ROOM_DELETED_QUEUE = "chat_room_deleted_queue"
CHAT_ROOM_RENAMED_QUEUE = "chat_room_renamed_queue"
MEMBER_REMOVED_QUEUE = "member_removed_queue"
MEMBER_LEFT_QUEUE = "member_left_queue"
TRANSLATION_REQUEST_QUEUE = "translation_request_queue"
TRANSLATION_COMPLETED_QUEUE = "translation_completed_queue"


def get_rabbit_connection():
    """
    Establish a connection to RabbitMQ using credentials from settings.
    """
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host="rabbitmq",
        port=5672,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


def _publish_to_queue(queue_name, message_data):
    """
    Generic helper: declare the specified queue and publish the message.
    """
    connection = None
    try:
        logger.debug(f"Connecting to RabbitMQ to publish to {queue_name}")
        connection = get_rabbit_connection()
        channel = connection.channel()

        # Declare the queue as durable
        channel.queue_declare(queue=queue_name, durable=True)

        body = json.dumps(message_data)
        logger.debug(f"Publishing message to '{queue_name}': {body}")

        channel.basic_publish(exchange="", routing_key=queue_name, body=body)
        logger.debug("Message published successfully")
    except Exception as e:
        logger.error(f"Failed to publish message to {queue_name}: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
        logger.debug("RabbitMQ connection closed")
        logger.info(f"Published message to '{queue_name}'")


def publish_chat_room_created(room_id, room_name, admin_id):
    """
    Publishes an event indicating that a new chat room has been created.
    """
    message_data = {
        "event": "chat_room_created",
        "room_id": room_id,
        "room_name": room_name,
        "admin_id": admin_id,
    }
    _publish_to_queue(CHAT_ROOM_CREATED_QUEUE, message_data)


def publish_user_invited(user_id, room_id, room_name):
    """
    Publishes an event indicating that a user has been invited to a chat room.
    """
    message_data = {
        "event": "user_invited",
        "user_id": user_id,
        "room_id": room_id,
        "room_name": room_name,
    }
    _publish_to_queue(USER_INVITED_QUEUE, message_data)


def publish_new_message(message_id, room_id, user_id, content):
    """
    Publishes an event indicating that a new message has been created in a room.
    """
    message_data = {
        "event": "new_message",
        "message_id": message_id,
        "room_id": room_id,
        "user_id": user_id,
        "content": content,
    }
    _publish_to_queue(NEW_MESSAGE_QUEUE, message_data)


def publish_message_processed(message_id, room_id, processed_info=None):
    """
    Publishes an event that a message has been processed (e.g., saved, translated, etc.).
    """
    message_data = {
        "event": "message_processed",
        "message_id": message_id,
        "room_id": room_id,
        "processed_info": processed_info or {},
    }
    _publish_to_queue(MESSAGE_PROCESSED_QUEUE, message_data)


def publish_chat_room_deleted(room_id):
    """
    Publish an event when a chat room is deleted.
    """
    message_data = {
        "event": "chat_room_deleted",
        "room_id": room_id,
    }
    _publish_to_queue(CHAT_ROOM_DELETED_QUEUE, message_data)


def publish_chat_room_renamed(room_id, old_name, new_name):
    """
    Publish an event when a chat room is renamed.
    """
    message_data = {
        "event": "chat_room_renamed",
        "room_id": room_id,
        "old_name": old_name,
        "new_name": new_name,
    }
    _publish_to_queue(CHAT_ROOM_RENAMED_QUEUE, message_data)


def publish_member_removed(room_id, user_id):
    """
    Publish an event when a member is removed by the admin.
    """
    message_data = {
        "event": "member_removed",
        "room_id": room_id,
        "user_id": user_id,
    }
    _publish_to_queue(MEMBER_REMOVED_QUEUE, message_data)


def publish_member_left(room_id, user_id):
    """
    Publish an event when a member leaves the room on their own.
    """
    message_data = {
        "event": "member_left",
        "room_id": room_id,
        "user_id": user_id,
    }
    _publish_to_queue(MEMBER_LEFT_QUEUE, message_data)


# (Optional) Retain your existing functions for backward compatibility:
def send_notification(notification_type, message):
    """
    Original function that maps a notification type to a queue.
    """
    queue_name = f"{notification_type}_notifications"
    _publish_to_queue(queue_name, message)


def send_translation_request(text, lang, room_id, user_id):
    message_data = {
        "event": "translation_request",
        "text": text,
        "lang": lang,
        "room_id": room_id,
        "message_id": str(uuid.uuid4()),
        "correlation_id": str(uuid.uuid4()),
        "user_id": user_id,
    }
    _publish_to_queue(TRANSLATION_REQUEST_QUEUE, message_data)
