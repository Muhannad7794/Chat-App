import React, { useState, useEffect } from "react";
import { Button, Container, ListGroup } from "react-bootstrap";
import { useNavigate } from "react-router-dom"; // Import useNavigate for navigation

const ChatRooms = ({ token }) => {
  const [chatRooms, setChatRooms] = useState([]);
  const navigate = useNavigate(); // Initialize navigate function

  // Move fetchChatRooms definition outside of useEffect
  const fetchChatRooms = async () => {
    const response = await fetch("http://localhost:8002/api/chat/rooms/", {
      headers: { Authorization: `Token ${token}` },
    });
    const data = await response.json();
    if (response.ok) {
      setChatRooms(data);
    } else {
      alert("Failed to fetch chat rooms");
    }
  };

  useEffect(() => {
    fetchChatRooms();
  }, [token, fetchChatRooms]); // Include fetchChatRooms as a dependency if it uses variables that could change

  const handleCreateRoom = async () => {
    const response = await fetch("http://localhost:8002/api/chat/rooms/", {
      method: "POST",
      headers: {
        Authorization: `Token ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name: "New Room" }), // Assuming the API needs a name
    });
    if (response.ok) {
      alert("Room created successfully!");
      fetchChatRooms(); // Refresh the list after creation
    } else {
      alert("Failed to create room");
    }
  };

  const handleRoomClick = (roomId) => {
    // Navigate to the room-specific Messages view
    navigate(`/chat-rooms/${roomId}/messages`);
  };

  return (
    <Container>
      <Button onClick={handleCreateRoom}>Create Chat Room</Button>
      <ListGroup>
        {chatRooms.map((room) => (
          <ListGroup.Item
            key={room.id}
            action
            onClick={() => handleRoomClick(room.id)}
          >
            {room.name}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
};

export default ChatRooms;
