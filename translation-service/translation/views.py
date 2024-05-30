# translation/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.http import JsonResponse
import requests
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from django.conf import settings
import pika
import logging


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def handle_translation_request(request):
    try:
        data = json.loads(request.body)
        text = data["text"]
        target_lang = data["lang"]

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
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
        logger.debug(f"Published message: {data}")

        def on_response(ch, method, props, body):
            if correlation_id == props.correlation_id:
                response = json.loads(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                connection.close()
                logger.debug(f"Received response: {response}")
                return JsonResponse({"translated_text": response["translated_text"]})

        channel.basic_consume(
            queue=callback_queue,
            on_message_callback=on_response,
            auto_ack=False,
        )

        logger.debug("Awaiting translation response")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Failed to handle translation request: {e}")
        return JsonResponse({"error": str(e)}, status=500)


class LanguagePreferenceAPI(APIView):
    def post(self, request, room_id):
        user_id = request.user.id
        language = request.data.get("language", "default")
        cache_key = f"user_{user_id}_room_{room_id}_lang"
        cache.set(cache_key, language)
        return Response(
            {"message": "Language preference set successfully"},
            status=status.HTTP_200_OK,
        )

    def get(self, request, room_id):
        user_id = request.user.id
        cache_key = f"user_{user_id}_room_{room_id}_lang"
        language = cache.get(cache_key, "default")
        return Response({"language": language}, status=status.HTTP_200_OK)


def translate_message(text, target_lang):
    endpoint = settings.AZURE_TRANSLATOR_ENDPOINT
    path = f"/translate?api-version=3.0&to={target_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }
    body = [{"text": text}]
    response = requests.post(f"{endpoint}{path}", headers=headers, json=body)
    response_json = response.json()
    return response_json[0]["translations"][0]["text"] if response_json else text
