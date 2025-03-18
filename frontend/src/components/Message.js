import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, Dropdown } from "react-bootstrap";
import axios from "axios";

const Messages = ({ token, currentUsername }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [language, setLanguage] = useState("default");
  const [usersMap, setUsersMap] = useState({}); // Mapping: user ID -> username
  const { roomId } = useParams();

  // Fetch messages
  useEffect(() => {
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
    fetchMessages();
  }, [token, roomId, language]);

  // Fetch user mapping from the API endpoint (adjust the URL if needed)
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get("http://localhost:8001/api/users/", {
          headers: { Authorization: `Token ${token}` },
        });
        const users = response.data;
        // Build mapping: user id -> username
        const mapping = {};
        users.forEach((user) => {
          mapping[user.id] = user.username;
        });
        setUsersMap(mapping);
      } catch (error) {
        console.error("Failed to fetch users mapping:", error);
      }
    };
    fetchUsers();
  }, [token]);

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    try {
      await axios.post(
        `http://localhost:8002/api/chat/set-language/`,
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

  const handleSendMessage = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(
        `http://localhost:8002/api/chat/messages/`,
        { content: newMessage, chat_room: roomId },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setMessages([...messages, response.data]);
      setNewMessage("");
    } catch (error) {
      console.error("Failed to send message:", error);
      alert("Failed to send message");
    }
  };

  const languages = ["en", "es", "fr", "de", "it", "ru", "zh", "ar", "ja"];

  // Function to assign a consistent color based on a username string
  const getUserColor = (username) => {
    if (!username) return "#6c757d"; // default grey if username is missing
    const colors = [
      "#007bff",
      "#28a745",
      "#dc3545",
      "#ffc107",
      "#6f42c1",
      "#17a2b8",
    ]; // remember to make it adynamic array not hard coded values
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
          // If msg.sender is an object with username, use it.
          // Otherwise, if it’s just an ID, look it up in usersMap.
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
          // Determine message alignment: right for the current user, left for others.
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
