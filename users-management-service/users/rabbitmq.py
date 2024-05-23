# uers/rabbitmq.py

import pika
import json
from django.conf import settings


def get_rabbit_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        settings.RABBITMQ_HOST, settings.RABBITMQ_PORT, "/", credentials
    )
    return pika.BlockingConnection(parameters)


def send_notification(queue, message):
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ),
    )
    connection.close()
