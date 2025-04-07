# consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import pika

from .translation_handler import get_user_language, translate_message
from .dispatch import (
    get_rabbit_connection,
    CHAT_ROOM_CREATED_QUEUE,
    USER_INVITED_QUEUE,
    NEW_MESSAGE_QUEUE,
    MESSAGE_PROCESSED_QUEUE,
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_id = self.scope["user"].id
        room_id = self.room_name

        try:
            translated_message = await self.fetch_and_translate_message(
                user_id, room_id, message
            )
        except Exception as e:
            logger.error(f"Error translating message: {e}")
            translated_message = message  # fallback

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": translated_message},
        )

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    async def fetch_and_translate_message(self, user_id, room_id, message):
        target_language = await get_user_language(user_id, room_id)
        if target_language and target_language != "default":
            return await translate_message(message, target_language)
        return message

    async def handle_translated_message(self, translated_data):
        translated_message = json.loads(translated_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": translated_message["text"]},
        )


def chat_room_deleted_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[chat_room_deleted_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Implement additional logic (e.g., cleanup, analytics) if needed.
    except Exception as e:
        logger.error(f"Error processing chat_room_deleted event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def chat_room_renamed_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[chat_room_renamed_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Implement logic: update caches, inform connected clients, etc.
    except Exception as e:
        logger.error(f"Error processing chat_room_renamed event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def member_removed_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[member_removed_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Implement logic: notify user, update membership state, etc.
    except Exception as e:
        logger.error(f"Error processing member_removed event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def member_left_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[member_left_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # Implement logic: notify remaining members, update stats, etc.
    except Exception as e:
        logger.error(f"Error processing member_left event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def chat_room_created_callback(ch, method, properties, body):
    """
    Handle messages from CHAT_ROOM_CREATED_QUEUE.
    For example: Log them, do analytics, send push notifications, etc.
    """
    try:
        data = json.loads(body)
        logger.info(f"[chat_room_created_callback] Received: {data}")
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing chat_room_created: {e}")
        # Decide if you want to requeue or discard
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def user_invited_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[user_invited_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing user_invited: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def new_message_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[new_message_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing new_message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def message_processed_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[message_processed_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing message_processed: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_rabbitmq_consumer():
    """
    This function declares each queue and sets up consumption.
    Then it blocks indefinitely on `channel.start_consuming()`.
    """
    connection = get_rabbit_connection()
    channel = connection.channel()

    # Ensure each queue is declared (matching dispatch.py)
    channel.queue_declare(queue=CHAT_ROOM_CREATED_QUEUE, durable=True)
    channel.queue_declare(queue=USER_INVITED_QUEUE, durable=True)
    channel.queue_declare(queue=NEW_MESSAGE_QUEUE, durable=True)
    channel.queue_declare(queue=MESSAGE_PROCESSED_QUEUE, durable=True)
    channel.queue_declare(queue=CHAT_ROOM_DELETED_QUEUE, durable=True)
    channel.queue_declare(queue=CHAT_ROOM_RENAMED_QUEUE, durable=True)
    channel.queue_declare(queue=MEMBER_REMOVED_QUEUE, durable=True)
    channel.queue_declare(queue=MEMBER_LEFT_QUEUE, durable=True)

    # Set up the callbacks for each queue
    for q in queues:
        channel.queue_declare(queue=q, durable=True)

    # Attach callbacks to the respective queues
    channel.basic_consume(
        queue=CHAT_ROOM_CREATED_QUEUE, on_message_callback=chat_room_created_callback
    )
    channel.basic_consume(
        queue=USER_INVITED_QUEUE, on_message_callback=user_invited_callback
    )
    channel.basic_consume(
        queue=NEW_MESSAGE_QUEUE, on_message_callback=new_message_callback
    )
    channel.basic_consume(
        queue=MESSAGE_PROCESSED_QUEUE, on_message_callback=message_processed_callback
    )
    channel.basic_consume(
        queue=CHAT_ROOM_DELETED_QUEUE, on_message_callback=chat_room_deleted_callback
    )
    channel.basic_consume(
        queue=CHAT_ROOM_RENAMED_QUEUE, on_message_callback=chat_room_renamed_callback
    )
    channel.basic_consume(
        queue=MEMBER_REMOVED_QUEUE, on_message_callback=member_removed_callback
    )
    channel.basic_consume(
        queue=MEMBER_LEFT_QUEUE, on_message_callback=member_left_callback
    )

    logger.info("RabbitMQ consumers are running and waiting for messages...")
    channel.start_consuming()
