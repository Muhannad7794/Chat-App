import json
import requests
from django.conf import settings
from .services import send_notification, send_translation_request


def get_language_preference(user_id, room_id):
    # Fetch the language preference from a cache or a settings database
    # Placeholder for cache retrieval logic
    pass


def set_language_preference(user_id, room_id, language_code):
    # Set the language preference in a cache or a settings database
    # Placeholder for cache setting logic
    pass


def translate_message(message, target_language):
    """Send a translation request to Azure Translation API."""
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }
    body = [{"text": message}]
    endpoint = f"{settings.AZURE_TRANSLATOR_ENDPOINT}/translate?api-version=3.0&to={target_language}"
    response = requests.post(endpoint, headers=headers, json=body)
    if response.status_code == 200:
        translated_text = response.json()[0]["translations"][0]["text"]
        return translated_text
    else:
        return message  # Fallback to the original message if translation fails


def handle_translation_response(translated_message, user_id, room_id):
    # Logic to send the translated message back to the client
    send_notification(
        "translated_message",
        {"room_id": room_id, "user_id": user_id, "message": translated_message},
    )
