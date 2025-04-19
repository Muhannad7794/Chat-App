#!/bin/sh

echo "Waiting for RabbitMQ to be ready..."

until nc -z rabbitmq 5672; do
  echo "RabbitMQ not available yet — sleeping"
  sleep 2
done

echo "RabbitMQ is up — starting worker"
python manage.py run_translation_worker
