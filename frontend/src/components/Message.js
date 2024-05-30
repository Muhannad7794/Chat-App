// frontend/src/components/Message.js
import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, ListGroup, Dropdown } from "react-bootstrap";
import axios from "axios"; // Using axios for HTTP requests

const Messages = ({ token }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [language, setLanguage] = useState("default");
  const { roomId } = useParams(); // Extract roomId from the URL

  useEffect(() => {
    fetchMessages();
  }, [token, roomId, language]);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8002/api/chat/messages/`,
        {
          params: { chat_room: roomId, lang: language },
          headers: { Authorization: `Token ${token}` },
        }
      );
      setMessages(response.data);
    } catch (error) {
      console.error("Failed to fetch messages:", error);
      alert("Failed to fetch messages");
    }
  };

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    try {
      await axios.post(
        `http://localhost:8002/api/chat/set-language/`,
        {
          chat_room: roomId,
          language: newLanguage,
        },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
    } catch (error) {
      console.error("Failed to set language:", error);
    }
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(
        `http://localhost:8002/api/chat/messages/`,
        {
          content: newMessage,
          chat_room: roomId,
        },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setMessages([...messages, response.data]); // Append new message to local state
      setNewMessage(""); // Clear input field
    } catch (error) {
      console.error("Failed to send message:", error);
      alert("Failed to send message");
    }
  };

  const languages = ["en", "es", "fr", "de", "it", "ru", "zh", "ar", "ja"]; // Expanded with additional global languages

  return (
    <Container>
      <Dropdown>
        <Dropdown.Toggle variant="success" id="dropdown-basic">
          Language
        </Dropdown.Toggle>
        <Dropdown.Menu>
          {languages.map((lang) => (
            <Dropdown.Item
              key={lang}
              onClick={() => handleLanguageChange(lang)}
            >
              {lang.toUpperCase()}
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown>
      <ListGroup>
        {messages.map((msg) => (
          <ListGroup.Item key={msg.id}>
            {msg.sender.username}: {msg.content}
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
