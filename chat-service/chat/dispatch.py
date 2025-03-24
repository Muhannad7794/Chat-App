import pika
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Constants for each queue name (you can rename them as you wish)
CHAT_ROOM_CREATED_QUEUE = "chat_room_created_queue"
USER_INVITED_QUEUE = "user_invited_queue"
NEW_MESSAGE_QUEUE = "new_message_queue"
MESSAGE_PROCESSED_QUEUE = "message_processed_queue"
# ... add more if needed, e.g. "chat_room_deleted_queue", etc.


def get_rabbit_connection():
    """
    Establishes a connection to RabbitMQ using credentials from settings.
    """
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


#
# New helper function for publishing to any queue
#
def _publish_to_queue(queue_name, message_data):
    """
    Opens a connection, declares the queue (durable),
    publishes the message, and closes the connection.
    """
    connection = None
    try:
        logger.debug(f"Connecting to RabbitMQ to publish to {queue_name}")
        connection = get_rabbit_connection()
        channel = connection.channel()

        # Ensure queue is declared (durable) so messages persist
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


#
# 1. Publish event when a new chat room is created
#
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


#
# 2. Publish event when a user is invited to a chat room
#
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


#
# 3. Publish event when a new message is sent
#
def publish_new_message(message_id, room_id, sender_id, content):
    """
    Publishes an event indicating that a new message has been created in a room.
    """
    message_data = {
        "event": "new_message",
        "message_id": message_id,
        "room_id": room_id,
        "sender_id": sender_id,
        "content": content,
    }
    _publish_to_queue(NEW_MESSAGE_QUEUE, message_data)


#
# 4. Publish event when a message is processed or stored
#
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


#
# (Optional) Keep your existing functions if still needed:
#
def send_notification(notification_type, message):
    """
    Original function. Could be left here for backward compatibility
    or replaced by more specific queue-based methods.
    """
    queue_name = f"{notification_type}_notifications"
    _publish_to_queue(queue_name, message)


def send_translation_request(text, target_language, room_id, user_id):
    """
    Original function for translation requests.
    """
    queue_name = "translation_request_queue"
    message = {
        "text": text,
        "lang": target_language,
        "room_id": room_id,
        "user_id": user_id,
    }
    _publish_to_queue(queue_name, message)