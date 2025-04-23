# test/unit_test/test_send_to_rabbitmq.py

import pytest
import json
from unittest.mock import AsyncMock, patch
from chat.consumers import ChatConsumer


@pytest.mark.asyncio
@patch("chat.consumers.aio_pika.connect_robust")
async def test_send_to_rabbitmq_dispatch(mock_connect):
    # Setup mock objects
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_queue = AsyncMock()

    mock_connect.return_value.__aenter__.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel
    mock_channel.declare_queue.return_value = mock_queue

    # Instantiate consumer
    consumer = ChatConsumer(scope={"type": "websocket"})
    await consumer.__call__()  # required to initialize consumer state

    payload = {
        "user_id": 1,
        "room_id": 2,
        "text": "hello",
        "lang": "es",
        "correlation_id": "123",
        "message_id": 42,
    }

    await consumer.send_to_rabbitmq(payload)

    mock_connect.assert_called_once()
    mock_channel.declare_queue.assert_called_once()
    mock_channel.default_exchange.publish.assert_called_once()

    sent_msg = mock_channel.default_exchange.publish.call_args[0][0]
    assert json.loads(sent_msg.body.decode()) == payload
