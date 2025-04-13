import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, Dropdown } from "react-bootstrap";
import axios from "axios";

const Messages = ({ token, currentUsername }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  // The language state now defaults to "original" meaning "show messages as sent"
  const [language, setLanguage] = useState("original");
  const [usersMap, setUsersMap] = useState({}); // Mapping: user ID -> username
  const { roomId } = useParams();
  const ws = useRef(null);

  // Function to fetch messages from backend
  const fetchMessages = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8002/api/chat/messages/",
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

  // Fetch messages initially and re-fetch when token, roomId, or language changes.
  useEffect(() => {
    fetchMessages();
  }, [token, roomId, language]);

  // Set up WebSocket connection for real‑time translation updates.
  useEffect(() => {
    if (roomId) {
      // Make sure this URL matches your Channels routing in the chat service.
      ws.current = new WebSocket(`ws://localhost:8002/ws/chat/${roomId}/`);
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "translation_update") {
          console.log("Received translation update:", data);
          // When a translation update is received, re‑fetch messages.
          fetchMessages();
        }
      };
      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
      return () => {
        if (ws.current) ws.current.close();
      };
    }
  }, [roomId]);

  // Fetch the user mapping data so we can display usernames with colors.
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get("http://localhost:8001/api/users/", {
          headers: { Authorization: `Token ${token}` },
        });
        const mapping = {};
        response.data.forEach((user) => {
          mapping[user.id] = user.username;
        });
        setUsersMap(mapping);
      } catch (error) {
        console.error("Failed to fetch users mapping:", error);
      }
    };
    fetchUsers();
  }, [token]);

  // Handle a change in language selection.
  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    try {
      // POST language preference change (do not hardcode a target language)
      await axios.post(
        "http://localhost:8002/api/chat/set-language/",
        { chat_room: roomId, language: newLanguage },
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

  // Handle sending a new message.
  const handleSendMessage = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(
        "http://localhost:8002/api/chat/messages/",
        { content: newMessage, chat_room: roomId },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      // Append the new message to the messages state.
      setMessages([...messages, response.data]);
      setNewMessage("");
    } catch (error) {
      console.error("Failed to send message:", error);
      alert("Failed to send message");
    }
  };

  // List of languages for the dropdown.
  const languages = ["en", "es", "fr", "de", "it", "ru", "zh", "ar", "ja"];

  // Helper function to assign a consistent color to usernames.
  const getUserColor = (username) => {
    if (!username) return "#6c757d"; // Default grey if username is missing.
    const colors = [
      "#007bff",
      "#28a745",
      "#dc3545",
      "#ffc107",
      "#6f42c1",
      "#17a2b8",
    ];
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colors.length;
    return colors[index];
  };

  return (
    <Container>
      <Dropdown className="mb-3">
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
      <div>
        {messages.map((msg) => {
          let senderUsername = "";
          if (
            msg.sender &&
            typeof msg.sender === "object" &&
            msg.sender.username
          ) {
            senderUsername = msg.sender.username;
          } else if (msg.sender) {
            senderUsername = usersMap[msg.sender] || msg.sender;
          } else {
            senderUsername = "Unknown";
          }
          // Right-align messages from the current user.
          const isCurrentUser = senderUsername === currentUsername;
          const alignment = isCurrentUser ? "flex-end" : "flex-start";
          return (
            <div
              key={msg.id}
              style={{
                display: "flex",
                justifyContent: alignment,
                marginBottom: "10px",
              }}
            >
              <div
                style={{
                  backgroundColor: getUserColor(senderUsername),
                  color: "#fff",
                  padding: "10px",
                  borderRadius: "10px",
                  maxWidth: "60%",
                }}
              >
                <strong>{senderUsername}</strong>
                <p style={{ margin: 0 }}>{msg.content}</p>
              </div>
            </div>
          );
        })}
      </div>
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
