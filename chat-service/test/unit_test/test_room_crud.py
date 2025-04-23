# test/unit_test/test_room_crud.py

import pytest
from rest_framework.test import APIClient
from chat.models import ChatRoom
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="room_owner", password="securepass")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def chat_room(user):
    return ChatRoom.objects.create(name="Initial Room", created_by=user)


def test_create_room(auth_client):
    url = "/api/chat/create-room/"
    payload = {"name": "New Room"}

    response = auth_client.post(url, payload, format="json")

    assert response.status_code == 201
    assert ChatRoom.objects.filter(name="New Room").exists()


def test_rename_room(auth_client, chat_room):
    url = f"/api/chat/rename-room/{chat_room.id}/"
    payload = {"new_name": "Renamed Room"}

    response = auth_client.put(url, payload, format="json")

    assert response.status_code == 200
    chat_room.refresh_from_db()
    assert chat_room.name == "Renamed Room"


def test_delete_room(auth_client, chat_room):
    url = f"/api/chat/delete-room/{chat_room.id}/"

    response = auth_client.delete(url)

    assert response.status_code == 204
    assert not ChatRoom.objects.filter(id=chat_room.id).exists()
