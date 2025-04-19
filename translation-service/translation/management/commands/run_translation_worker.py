# translation/management/commands/run_translation_worker.py

from django.core.management.base import BaseCommand
import pika  # type: ignore
import json
import uuid
import logging
from django.conf import settings
from django.core.cache import cache
from translation.translation_handler import (
    translate_message,
    save_translated_result_to_cache,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the translation worker that processes messages from the translation_request_queue and publishes results."

    def handle(self, *args, **options):
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host="rabbitmq",
                port=5672,
                credentials=credentials,
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            request_queue = "translation_request_queue"
            completed_queue = "translation_completed_queue"
            channel.queue_declare(queue=request_queue, durable=True)
            channel.queue_declare(queue=completed_queue, durable=True)

            logger.info("Translation worker started. Waiting for messages...")

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body)
                    text = payload.get("text")
                    target_lang = payload.get("lang")
                    room_id = payload.get("room_id")
                    message_id = payload.get("message_id")
                    correlation_id = payload.get("correlation_id")
                    logger.info(f"Received translation request: {payload}")

                    # Call Azure Translator API synchronously.
                    translated_text = translate_message(text, target_lang)
                    save_translated_result_to_cache(
                        message_id, payload["user_id"], translated_text
                    )
                    logger.info(
                        f"AZURE_TRANSLATOR_KEY: {settings.AZURE_TRANSLATOR_KEY}"
                    )

                    # Optionally, save the result in cache using the correlation_id (for GET polling).
                    cache.set(
                        f"translation_response:{correlation_id}",
                        translated_text,
                        timeout=300,
                    )
                    logger.info(
                        f"Stored translation in Redis under key translation_response:{correlation_id}"
                    )

                    # Build completed event payload.
                    event = {
                        "type": "translation_update",
                        "correlation_id": correlation_id,
                        "room_id": room_id,
                        "user_id": payload["user_id"],
                        "message_id": message_id,
                        "translated_text": translated_text,
                    }
                    # Publish to the completed queue.
                    channel.basic_publish(
                        exchange="",
                        routing_key=completed_queue,
                        body=json.dumps(event),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
                    logger.info(f"Published translation completed event: {event}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error processing translation request: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=request_queue, on_message_callback=callback)
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Translation worker encountered a fatal error: {e}")
