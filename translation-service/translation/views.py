# translation/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import uuid
import json
import uuid
from django.conf import settings
import pika
import logging

logger = logging.getLogger(__name__)


class TranslationAPIView(APIView):
    """
    Synchronous endpoint to trigger a translation request.
    Accepts JSON payload: {"text": "...", "lang": "es"}.
    Returns a correlation_id.
    NOTE: In production the chat service should publish translation requests
          asynchronously via RabbitMQ.
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        text = data.get("text")
        lang = data.get("lang")
        if not text or not lang:
            return Response(
                {"error": "Both text and lang are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        correlation_id = str(uuid.uuid4())
        # For testing, we can perform synchronous translation.
        from .translation_handler import translate_text

        translated_text = translate_text(text, lang)
        # Optionally store in cache keyed by correlation_id
        cache.set(correlation_id, translated_text, timeout=300)
        return Response(
            {
                "correlation_id": correlation_id,
                "translated_text": translated_text,
                "status": "completed",
            },
            status=status.HTTP_200_OK,
        )


class TranslationResultAPIView(APIView):
    """
    Endpoint to fetch translation results from cache.
    GET /translation/result/<correlation_id>/
    """

    def get(self, request, correlation_id, *args, **kwargs):
        result = cache.get(correlation_id)
        if result is None:
            return Response({"status": "processing"}, status=status.HTTP_202_ACCEPTED)
        return Response({"translated_text": result}, status=status.HTTP_200_OK)
