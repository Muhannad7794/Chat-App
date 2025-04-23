import json
import pytest
from channels.testing import WebsocketCommunicator
from chat_manager.asgi import application
from chat.models import ChatRoom
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

pytestmark = pytest.mark.asyncio


@pytest.mark.django_db(transaction=True)
async def test_chat_websocket_authenticated_message_flow():
    # Setup user
    User = get_user_model()
    user = User.objects.create_user(username="tester", password="password")
    token, _ = Token.objects.get_or_create(user=user)

    # Setup chat room
    chat_room = ChatRoom.objects.create(name="Test Room")

    # Create WebSocket communicator with token query param
    communicator = WebsocketCommunicator(
        application=application, path=f"/ws/chat/{chat_room.id}/?token={token.key}"
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Send a valid message
    await communicator.send_json_to({"message": "Hello world!"})

    # Receive the broadcasted message
    response = await communicator.receive_json_from()
    assert response["type"] == "chat_message"
    assert response["message"] == "Hello world!"
    assert response["room_id"] == str(chat_room.id)
    assert response["username"] == "tester"
    assert "message_id" in response

    await communicator.disconnect()
