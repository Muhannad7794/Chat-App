import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .translation_handler import get_user_language, translate_message

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
            translated_message = (
                message  # Fallback to original message in case of error
            )

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
