import pika
import json
import logging
from .views import translate_message

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def start_translation_worker():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="translation_requests", durable=True)
        logger.debug("Connected to RabbitMQ and declared queue.")

        def on_request(ch, method, properties, body):
            logger.debug(f"Received message: {body}")
            data = json.loads(body)
            translated_text = translate_message(data["text"], data["lang"])

            response = {
                "translated_text": translated_text,
                "correlation_id": properties.correlation_id,
            }

            ch.basic_publish(
                exchange="",
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                ),
                body=json.dumps(response),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Sent response: {response}")

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue="translation_requests", on_message_callback=on_request
        )

        logger.debug("Awaiting translation requests")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Failed to start translation worker: {e}")


if __name__ == "__main__":
    start_translation_worker()
