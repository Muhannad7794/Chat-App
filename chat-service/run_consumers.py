# run_consumers.py
# chat-service/run_consumers.py
import os
import django
import logging
import traceback

# Set environment and initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_manager.settings")
django.setup()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from chat.consumers import start_rabbitmq_consumer

    logger.info("[run_consumers.py] Starting RabbitMQ consumer...")
    start_rabbitmq_consumer()
except Exception as e:
    logger.error("[run_consumers.py] Failed to start consumer due to:")
    traceback.print_exc()
