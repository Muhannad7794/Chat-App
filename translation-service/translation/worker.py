import pika
import json
from external_translation_api import translate_message  # Placeholder for actual import


def start_translation_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.queue_declare(queue="translation_requests", durable=True)

    def on_request(ch, method, properties, body):
        data = json.loads(body)
        translated_text = translate_message(data["text"], data["lang"])

        ch.basic_publish(
            exchange="",
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=json.dumps(translated_text),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="translation_requests", on_message_callback=on_request)

    print(" [x] Awaiting translation requests")
    channel.start_consuming()


if __name__ == "__main__":
    start_translation_worker()
