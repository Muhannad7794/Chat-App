import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache


class TranslationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"room_{self.room_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        message = content["message"]
        user_id = self.scope["user"].id
        cache_key = f"user_{user_id}_room_{self.room_id}_lang"
        target_lang = cache.get(cache_key, "en")

        # Assume translate_message is an async function to request translation
        translated_message = await translate_message(message, target_lang)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": translated_message, "user_id": user_id},
        )

    async def chat_message(self, event):
        await self.send_json({"message": event["message"], "user_id": event["user_id"]})
