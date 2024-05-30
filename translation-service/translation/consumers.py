import json
import pika
import uuid
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TranslationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"room_{self.room_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.debug(f"WebSocket connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.debug(f"WebSocket disconnected: {self.room_group_name}")

    async def receive_json(self, content):
        message = content["message"]
        user_id = self.scope["user"].id
        cache_key = f"user_{user_id}_room_{self.room_id}_lang"
        target_lang = cache.get(cache_key, "en")

        logger.debug(f"Received message to translate: {message}")

        translated_message = await self.send_translation_request(message, target_lang)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": translated_message, "user_id": user_id},
        )

    async def chat_message(self, event):
        await self.send_json({"message": event["message"], "user_id": event["user_id"]})

    async def send_translation_request(self, text, target_lang):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            channel = connection.channel()
            result = channel.queue_declare(queue="", exclusive=True)
            callback_queue = result.method.queue
            correlation_id = str(uuid.uuid4())

            channel.basic_publish(
                exchange="",
                routing_key="translation_requests",
                properties=pika.BasicProperties(
                    reply_to=callback_queue,
                    correlation_id=correlation_id,
                ),
                body=json.dumps({"text": text, "lang": target_lang}),
            )
            logger.debug(f"Published translation request: {text}")

            def on_response(ch, method, props, body):
                if correlation_id == props.correlation_id:
                    response = json.loads(body)
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    connection.close()
                    logger.debug(f"Received translation response: {response}")
                    return response["translated_text"]

            channel.basic_consume(
                queue=callback_queue,
                on_message_callback=on_response,
                auto_ack=False,
            )

            while True:
                method, properties, body = channel.basic_get(callback_queue)
                if body:
                    return json.loads(body)["translated_text"]
        except Exception as e:
            logger.error(f"Failed to send translation request: {e}")
            return text  # Return original text in case of failure
