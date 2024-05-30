# translation/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.http import JsonResponse
import requests
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


class LanguagePreferenceAPI(APIView):
    def post(self, request, room_id):
        user_id = request.user.id
        language = request.data.get("language", "en")  # Default to English
        cache_key = f"user_{user_id}_room_{room_id}_lang"
        cache.set(cache_key, language)
        return Response(
            {"message": "Language preference set successfully"},
            status=status.HTTP_200_OK,
        )

    def get(self, request, room_id):
        user_id = request.user.id
        cache_key = f"user_{user_id}_room_{room_id}_lang"
        language = cache.get(cache_key, "en")  # Default to English
        return Response({"language": language}, status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def handle_translation_request(request):
    data = json.loads(request.body)
    text = data.get("text")
    target_lang = data.get("lang")
    translated_text = translate_message(text, target_lang)
    return JsonResponse({"translated_text": translated_text})


def translate_message(text, target_lang):
    endpoint = settings.AZURE_TRANSLATOR_ENDPOINT
    path = "/translate?api-version=3.0&to=" + target_lang
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }
    body = [{"text": text}]
    request = requests.post(endpoint + path, headers=headers, json=body)
    response = request.json()
    return response[0]["translations"][0]["text"] if response else text
