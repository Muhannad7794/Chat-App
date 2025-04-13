# translation/translation_handler.py

import json
import requests
import uuid
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def translate_text(text, target_language):
    """
    Calls the Azure Translator API synchronously to translate the given text.
    If translation fails, logs the error and returns the original text.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json",
    }
    # Ensure that the endpoint URL does not have a trailing slash issue.
    endpoint = settings.AZURE_TRANSLATOR_ENDPOINT.rstrip("/")
    url = f"{endpoint}/translate?api-version=3.0&to={target_language}"
    body = [{"text": text}]
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
        translated_text = data[0]["translations"][0]["text"]
        return translated_text
    except Exception as e:
        logger.error(f"Error during Azure translation: {e}")
        return text  # Fallback to the original text if an error occurs

