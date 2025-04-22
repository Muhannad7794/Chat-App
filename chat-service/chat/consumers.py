# chat/consumers.py

import json
import asyncio
import uuid
import logging
import redis  # type: ignore
import pika  # type: ignore
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async, async_to_sync
from chat.translation_handler import get_language_preference

# queues imports
from .dispatch import (
    get_rabbit_connection,
    CHAT_ROOM_CREATED_QUEUE,
    CHAT_ROOM_DELETED_QUEUE,
    CHAT_ROOM_RENAMED_QUEUE,
    MEMBER_REMOVED_QUEUE,
    MEMBER_LEFT_QUEUE,
    USER_INVITED_QUEUE,
    NEW_MESSAGE_QUEUE,
    MESSAGE_PROCESSED_QUEUE,
    TRANSLATION_COMPLETED_QUEUE,
    LANGUAGE_CHANGE_NOTIFICATIONS_QUEUE,
    ROOM_RENAMED_NOTIFICATIONS_QUEUE,
    TRANSLATION_REQUEST_QUEUE,
)

REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 1

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            logger.warning("[connect] Rejected unauthenticated WebSocket connection")
            await self.close()
            return

        self.user = user
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.debug(
            f"[connect] User {user.username} connected to room {self.room_name}"
        )
        logger.info(
            f"[connect] User connected and added to group: {self.room_group_name}"
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        if hasattr(self, "user_room_group_name"):
            await self.channel_layer.group_discard(
                self.user_room_group_name, self.channel_name
            )
        logger.info(
            f"[disconnect] User {getattr(self, 'user', None)} disconnected from {getattr(self, 'room_group_name', None)}"
        )

    async def receive(self, text_data=None, bytes_data=None):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            logger.warning("[receive] Unauthenticated user")
            return

        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            if not message:
                logger.warning("[receive] Empty message")
                return

            room_id = self.room_name
            user_id = getattr(user, "id", None)
            username = getattr(user, "username", "anonymous")

            from chat.models import ChatRoom, Message

            chat_room = await sync_to_async(ChatRoom.objects.get)(id=room_id)

            # ✅ Fix: convert SimpleUser → actual User model instance
            User = get_user_model()
            real_user = await sync_to_async(User.objects.get)(id=user_id)

            saved_msg = await sync_to_async(Message.objects.create)(
                content=message,
                sender=real_user,
                chat_room=chat_room,
            )

            logger.info(
                f"[receive] Message saved: id={saved_msg.id} from {username} in room {room_id}"
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user_id": user_id,
                    "username": username,
                    "room_id": room_id,
                },
            )

            asyncio.create_task(self.trigger_translation(user_id, room_id, message))

        except json.JSONDecodeError:
            logger.error("[receive] Malformed JSON received")
        except Exception as e:
            logger.exception(f"[receive] Unexpected error: {e}")

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
        except Exception as e:
            logger.exception(f"[chat_message] Failed to send: {e}")

    async def translation_update(self, event):
        try:
            logger.info(
                f"[WS] Sending translated message to client: {event['message']}"
            )
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "translation_update",
                        "message": event["message"],
                    }
                )
            )
        except Exception as e:
            logger.exception(f"[translation_update] Failed to send update: {e}")

    async def trigger_translation(self, user_id, room_id, message):
        try:
            lang = await sync_to_async(get_language_preference)(user_id, room_id)
            payload = {
                "user_id": user_id,
                "room_id": room_id,
                "text": message,
                "lang": lang,
                "correlation_id": str(uuid.uuid4()),
            }
            await sync_to_async(self.send_to_rabbitmq)(payload)
            logger.debug(
                f"[trigger_translation] Triggered translation for user {user_id} in room {room_id}"
            )
        except Exception as e:
            logger.exception(
                f"[trigger_translation] Failed to dispatch translation request: {e}"
            )

    def send_to_rabbitmq(self, payload):
        try:
            logger.info(f"[send_to_rabbitmq] Dispatching: {payload}")
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
                    delivery_mode=2, content_type="application/json"
                ),
            )
            connection.close()
        except Exception as e:
            logger.exception(f"[send_to_rabbitmq] Error: {e}")


# ---------- RabbitMQ Callback Handlers (Sync Context) ----------


def translation_completed_callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logger.info(f"[translation_completed_callback] Received: {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

        room_id = data.get("room_id")
        translated_text = data.get("translated_text")
        message_id = data.get("message_id")

        group_name = f"chat_{room_id}"
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "translation_update",
                "message_id": message_id,
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
        CHAT_ROOM_CREATED_QUEUE: default_callback(CHAT_ROOM_CREATED_QUEUE),
        CHAT_ROOM_DELETED_QUEUE: default_callback(CHAT_ROOM_DELETED_QUEUE),
        CHAT_ROOM_RENAMED_QUEUE: default_callback(CHAT_ROOM_RENAMED_QUEUE),
        MEMBER_REMOVED_QUEUE: default_callback(MEMBER_REMOVED_QUEUE),
        MEMBER_LEFT_QUEUE: default_callback(MEMBER_LEFT_QUEUE),
        USER_INVITED_QUEUE: default_callback(USER_INVITED_QUEUE),
        NEW_MESSAGE_QUEUE: default_callback(NEW_MESSAGE_QUEUE),
        MESSAGE_PROCESSED_QUEUE: default_callback(MESSAGE_PROCESSED_QUEUE),
        ROOM_RENAMED_NOTIFICATIONS_QUEUE: default_callback(
            ROOM_RENAMED_NOTIFICATIONS_QUEUE
        ),
        TRANSLATION_REQUEST_QUEUE: default_callback(TRANSLATION_REQUEST_QUEUE),
        TRANSLATION_COMPLETED_QUEUE: translation_completed_callback,  # Special case
        LANGUAGE_CHANGE_NOTIFICATIONS_QUEUE: language_change_callback,  # Special case
    }

    for queue, handler in queues.items():
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_consume(queue=queue, on_message_callback=handler)

    logger.info("RabbitMQ consumers running and listening to queues.")
    channel.start_consuming()
