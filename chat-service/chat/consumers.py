# chat/consumers.py
import json
import asyncio
import uuid
import logging
import redis  # type: ignore
import pika  # type: ignore
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async, async_to_sync
from chat.translation_handler import get_language_preference

# queues imports
from .dispatch import (
    get_rabbit_connection,
    send_translation_request,
    CHAT_ROOM_CREATED_QUEUE,
    CHAT_ROOM_DELETED_QUEUE,
    CHAT_ROOM_RENAMED_QUEUE,
    MEMBER_REMOVED_QUEUE,
    MEMBER_LEFT_QUEUE,
    USER_INVITED_QUEUE,
    NEW_MESSAGE_QUEUE,
    MESSAGE_PROCESSED_QUEUE,
    TRANSLATION_COMPLETED_QUEUE,
)

REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 1
TRANSLATION_REQUEST_QUEUE = "translation_request_queue"
TRANSLATION_RESPONSE_TIMEOUT = 5

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        print("[WS DEBUG] scope user is:", user)

        if not user or not getattr(user, "is_authenticated", False):
            print("[WS DEBUG] Rejected due to unauthenticated")
            logger.warning("[connect] Rejected unauthenticated WebSocket connection")
            await self.close()
            return

        # Store user object
        self.user = user

        # Get room from URL route and set group name
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"

        # Add user to the channel group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept connection
        logger.debug(
            f"[connect] Accepted connection for user {user.username} in room {self.room_name}"
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Avoid attribute error in rare edge cases
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        if hasattr(self, "user_room_group_name"):
            await self.channel_layer.group_discard(
                self.user_room_group_name, self.channel_name
            )

        logger.info(
            f"[disconnect] Disconnected user: {getattr(self, 'user', 'Unknown')} "
            f"from room: {getattr(self, 'room_group_name', 'Unknown')}"
        )

    async def chat_message(self, event):
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "chat_message",
                        "message": event["message"],
                        "user_id": event.get("user_id"),
                        "username": event.get("username"),
                    }
                )
            )
            logger.debug(f"[chat_message] Sent message to client: {event['message']}")
        except Exception as e:
            logger.exception(f"[chat_message] Error sending message: {e}")

    async def receive(self, text_data=None, bytes_data=None):
        user = self.scope.get("user")
        user_id = getattr(user, "id", None)

        if not user or not user.is_authenticated:
            logger.warning("[receive] Received message from unauthenticated user")
            return

        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()

            if not message:
                logger.warning("[receive] Empty message received.")
                return

            logger.info(
                f"[receive] Message from user {user_id} in room {self.room_name}"
            )

            # Translate the message
            translated_message = await self.fetch_and_translate_message(
                user_id, self.room_name, message
            )

            # Send to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": translated_message,
                    "original": message,
                    "user_id": user_id,
                    "username": getattr(user, "username", "anonymous"),
                    "room_id": self.room_name,
                },
            )

            logger.debug(
                f"[receive] Broadcasted translated message in room {self.room_group_name}"
            )

        except json.JSONDecodeError:
            logger.error("[receive] Invalid JSON received.")
        except Exception as e:
            logger.exception(f"[receive] Unexpected error: {e}")

    async def translation_update(self, event):
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "translation_update",
                        "message": event["message"],
                    }
                )
            )
        except Exception as e:
            logger.exception(f"[translation_update] Error sending: {e}")

    async def fetch_and_translate_message(self, user_id, room_id, message):
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[fetch_and_translate_message] ID: {correlation_id} from user {user_id}"
        )

        try:
            lang = await sync_to_async(get_language_preference)(user_id, room_id)
            logger.debug(f"[fetch_and_translate_message] Using language: {lang}")

            request_payload = {
                "user_id": user_id,
                "room_id": room_id,
                "text": message,
                "lang": lang,
                "correlation_id": correlation_id,
            }

            await sync_to_async(self.send_to_rabbitmq)(request_payload)

            redis_conn = await sync_to_async(redis.Redis)(
                host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
            )
            response_key = f"translation_response:{correlation_id}"

            for _ in range(TRANSLATION_RESPONSE_TIMEOUT * 10):
                translated = await sync_to_async(redis_conn.get)(response_key)
                if translated:
                    await sync_to_async(redis_conn.delete)(response_key)
                    return translated
                await asyncio.sleep(0.1)

            logger.warning(
                f"[fetch_and_translate_message] Timeout for {correlation_id} (key={response_key})"
            )
            return message  # Fallback

        except Exception as e:
            logger.exception(f"[fetch_and_translate_message] Error: {e}")
            return message

    def send_to_rabbitmq(self, payload):
        logger.info(f"[send_to_rabbitmq] Sending: {payload}")

        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
        )
        parameters = pika.ConnectionParameters(
            host="rabbitmq", port=5672, credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=TRANSLATION_REQUEST_QUEUE, durable=True)

        channel.basic_publish(
            exchange="",
            routing_key=TRANSLATION_REQUEST_QUEUE,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        connection.close()
        logger.info("[send_to_rabbitmq] Payload sent and connection closed.")


# ---------- RabbitMQ Callback Handlers (Sync Context) ----------


def translation_completed_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[translation_completed_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

        room_id = data.get("room_id")
        user_id = data.get("user_id")
        translated_text = data.get("translated_text")

        group_name = f"user_{user_id}_room_{room_id}"
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "translation_update",
                "message": translated_text,
            },
        )

    except Exception as e:
        logger.error(f"[translation_completed_callback] Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ---------- Other Queue Callbacks ----------


def default_callback(queue_name):
    def handler(ch, method, properties, body):
        try:
            data = json.loads(body)
            logger.info(f"[{queue_name}] Received: {data}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"[{queue_name}] Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    return handler


# ---------- Language‑Change Callback (Sync context) ----------


def language_change_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        user_id = data["user_id"]
        room_id = data["room_id"]
        new_lang = data["language_code"]

        # Avoid circular imports
        from chat.models import Message
        from .dispatch import send_translation_request

        for msg in Message.objects.filter(chat_room_id=room_id):
            send_translation_request(
                text=msg.content,
                lang=new_lang,
                room_id=room_id,
                user_id=user_id,
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"[language_change_callback] Error re‑translating backlog: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ---------- RabbitMQ Consumer Entry Point ----------


def start_rabbitmq_consumer():
    connection = get_rabbit_connection()
    channel = connection.channel()

    queues = {
        CHAT_ROOM_CREATED_QUEUE: default_callback("chat_room_created"),
        CHAT_ROOM_DELETED_QUEUE: default_callback("chat_room_deleted"),
        CHAT_ROOM_RENAMED_QUEUE: default_callback("chat_room_renamed"),
        MEMBER_REMOVED_QUEUE: default_callback("member_removed"),
        MEMBER_LEFT_QUEUE: default_callback("member_left"),
        USER_INVITED_QUEUE: default_callback("user_invited"),
        NEW_MESSAGE_QUEUE: default_callback("new_message"),
        MESSAGE_PROCESSED_QUEUE: default_callback("message_processed"),
        TRANSLATION_COMPLETED_QUEUE: translation_completed_callback,  # Special case
        "language_change_notifications": language_change_callback,
    }

    for queue, handler in queues.items():
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_consume(queue=queue, on_message_callback=handler)

    logger.info("RabbitMQ consumers running and listening to queues.")
    channel.start_consuming()
