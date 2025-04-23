# test/unit_test/test_language_preferences.py

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from chat.models import ChatRoom
from django.core.cache import cache

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="translator", password="securepass")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def chat_room():
    return ChatRoom.objects.create(name="Language Test Room")


def test_set_language_preference(auth_client, user, chat_room):
    url = "/api/chat/set-language/"
    payload = {
        "chat_room": chat_room.id,
        "language": "es",
    }

    response = auth_client.post(url, payload, format="json")

    assert response.status_code == 200
    cache_key = f"user_{user.id}_room_{chat_room.id}_lang"
    assert cache.get(cache_key) == "es"


def test_get_language_preference(auth_client, user, chat_room):
    cache_key = f"user_{user.id}_room_{chat_room.id}_lang"
    cache.set(cache_key, "de")

    url = f"/api/chat/get-language/?chat_room={chat_room.id}"
    response = auth_client.get(url)

    assert response.status_code == 200
    assert response.data["language"] == "de"
