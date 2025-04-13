# run_consumers.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_manager.settings")
django.setup()

from chat.consumers import start_rabbitmq_consumer

start_rabbitmq_consumer()
