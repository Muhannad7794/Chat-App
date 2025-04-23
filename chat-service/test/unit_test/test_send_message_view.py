# test/unit_test/test_send_message_view.py

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, Message

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def chat_room():
    return ChatRoom.objects.create(name="Test Room")


def test_send_message_success(auth_client, user, chat_room):
    url = "/api/chat/messages/"
    data = {"chat_room": chat_room.id, "content": "Hello World!"}

    response = auth_client.post(url, data, format="json")

    assert response.status_code == 201
    assert Message.objects.filter(chat_room=chat_room, sender=user).exists()
    assert response.data["content"] == "Hello World!"
