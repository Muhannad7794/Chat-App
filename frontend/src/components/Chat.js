// src/components/Chat.js
import React, { useState, useEffect } from "react";
import { Container, Form, Button, ListGroup } from "react-bootstrap";
import axios from "axios";

function Chat() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    // Fetch messages on load
    const fetchMessages = async () => {
      const result = await axios.get(
        `${process.env.REACT_APP_CHAT_SERVICE_URL}/api/chat/messages/`,
        {
          headers: { Authorization: `Token ${localStorage.getItem("token")}` },
        }
      );
      setMessages(result.data);
    };
    fetchMessages();
  }, []);

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!message) return;
    try {
      await axios.post(
        `${process.env.REACT_APP_CHAT_SERVICE_URL}/api/chat/messages/`,
        {
          content: message,
        },
        {
          headers: { Authorization: `Token ${localStorage.getItem("token")}` },
        }
      );
      setMessage("");
      setMessages([...messages, message]);
    } catch (error) {
      console.error("Failed to send message:", error);
      alert("Failed to send message! Check console for details.");
    }
  };

  return (
    <Container className="mt-5">
      <ListGroup>
        {messages.map((msg, index) => (
          <ListGroup.Item key={index}>{msg.content || msg}</ListGroup.Item>
        ))}
      </ListGroup>
      <Form onSubmit={sendMessage}>
        <Form.Group className="mt-3">
          <Form.Control
            type="text"
            placeholder="Type a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
          />
        </Form.Group>
        <Button variant="primary" type="submit" className="mt-3">
          Send
        </Button>
      </Form>
    </Container>
  );
}

export default Chat;
