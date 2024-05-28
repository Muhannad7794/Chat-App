import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, ListGroup } from "react-bootstrap";

const Messages = ({ token }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const { roomId } = useParams(); // Extract roomId from the URL

  useEffect(() => {
    // Part of the Messages component in React

    const fetchMessages = async () => {
      const response = await fetch(
        `http://localhost:8002/api/chat/messages/?chat_room=${roomId}`, // Now clearly specifying the room ID
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      } else {
        alert("Failed to fetch messages");
      }
    };

    const handleSendMessage = async (event) => {
      event.preventDefault();
      const response = await fetch(`http://localhost:8002/api/chat/messages/`, {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: newMessage,
          chat_room: roomId, // Ensure this is part of the body
        }),
      });
      if (response.ok) {
        const newMessage = await response.json();
        setMessages([...messages, newMessage]);
        setNewMessage("");
      } else {
        alert("Failed to send message");
      }
    };

    fetchMessages();
  }, [token, roomId]);

  const handleSendMessage = async (event) => {
    event.preventDefault();
    const messageData = {
      content: newMessage,
      chat_room: roomId, // This assumes roomId is correctly populated
    };

    const response = await fetch(`http://localhost:8002/api/chat/messages/`, {
      method: "POST",
      headers: {
        Authorization: `Token ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(messageData),
    });

    if (response.ok) {
      const newMessage = await response.json();
      setMessages([...messages, newMessage]); // Append new message to local state
      setNewMessage(""); // Clear input field
    } else {
      alert("Failed to send message");
    }
  };

  return (
    <Container>
      <ListGroup>
        {messages.map((msg) => (
          <ListGroup.Item key={msg.id}>
            {msg.sender}: {msg.content}
          </ListGroup.Item>
        ))}
      </ListGroup>
      <Form onSubmit={handleSendMessage}>
        <Form.Group className="mb-3" controlId="newMessage">
          <Form.Label>New Message</Form.Label>
          <Form.Control
            type="text"
            placeholder="Type a message"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
          />
        </Form.Group>
        <Button variant="primary" type="submit">
          Send
        </Button>
      </Form>
    </Container>
  );
};

export default Messages;
