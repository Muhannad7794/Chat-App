import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, ListGroup, Dropdown } from "react-bootstrap";

const Messages = ({ token }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [language, setLanguage] = useState("default");
  const { roomId } = useParams(); // Extract roomId from the URL

  useEffect(() => {
    fetchMessages();
    // Assuming there's an endpoint to fetch the current language setting
  }, [token, roomId, language]);

  const fetchMessages = async () => {
    const response = await fetch(
      `http://localhost:8002/api/chat/messages/?chat_room=${roomId}&lang=${language}`,
      { headers: { Authorization: `Token ${token}` } }
    );
    if (response.ok) {
      const data = await response.json();
      setMessages(data);
    } else {
      alert("Failed to fetch messages");
    }
  };

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    // Logic to update language setting and re-fetch messages
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();
    const messageData = {
      content: newMessage,
      chat_room: roomId,
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
      const newMsg = await response.json();
      setMessages([...messages, newMsg]); // Append new message to local state
      setNewMessage(""); // Clear input field
    } else {
      alert("Failed to send message");
    }
  };

  const languages = ["en", "es", "fr", "de"]; // Extend with all supported languages

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
