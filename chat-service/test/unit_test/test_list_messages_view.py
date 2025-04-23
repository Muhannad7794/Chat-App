# test/unit_test/test_list_messages_view.py

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, Message

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="viewer", password="pass123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def chat_room():
    return ChatRoom.objects.create(name="History Room")


@pytest.fixture
def messages(user, chat_room):
    return [
        Message.objects.create(content="First", sender=user, chat_room=chat_room),
        Message.objects.create(content="Second", sender=user, chat_room=chat_room),
    ]


def test_list_messages(auth_client, chat_room, messages):
    url = f"/api/chat/messages/?chat_room={chat_room.id}"

    response = auth_client.get(url)

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 2
    assert response.data[0]["content"] == "First"
