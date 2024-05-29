from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache


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
