import json
import pytest
from channels.testing import WebsocketCommunicator
from chat_manager.asgi import application
from chat.models import ChatRoom, Message
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receive_creates_message_and_broadcasts():
    # Setup: Create test user and chat room
    User = get_user_model()
    user = await sync_to_async(User.objects.create_user)(
        username="ws_test_user", password="pass"
    )
    room = await sync_to_async(ChatRoom.objects.create)(name="ws_room")

    # Simulate token auth by manually injecting scope
    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{room.id}/",
    )
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert connected

    # Send a message over WebSocket
    await communicator.send_json_to({"message": "Hello from test!"})

    # Receive the broadcasted chat_message
    response = await communicator.receive_json_from()

    assert response["type"] == "chat_message"
    assert response["message"] == "Hello from test!"
    assert response["room_id"] == str(room.id) or response["room_id"] == room.id
    assert response["user_id"] == user.id
    assert response["username"] == user.username

    # Check if Message was saved in the database
    count = await sync_to_async(Message.objects.count)()
    assert count == 1

    await communicator.disconnect()
