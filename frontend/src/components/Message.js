// Message.js
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Form, Button, Container, Dropdown } from "react-bootstrap";
import axios from "axios";

const Messages = ({ token, currentUsername }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [language, setLanguage] = useState("original");
  const [usersMap, setUsersMap] = useState({});
  const { roomId } = useParams();
  const ws = useRef(null);

  const fetchMessages = useCallback(async () => {
    try {
      const params = { chat_room: roomId };
      if (language !== "original") {
        params.lang = language;
      }

      const response = await axios.get(
        "http://localhost:8002/api/chat/messages/",
        {
          params,
          headers: { Authorization: `Token ${token}` },
        }
      );

      // Handle fallback to original if translation is missing
      const formatted = response.data.map((msg) => ({
        id: msg.id,
        original_content: msg.content,
        translated_content: msg.translated_content || null,
        sender: msg.sender,
      }));

      setMessages(formatted);
    } catch (error) {
      console.error("Failed to fetch messages:", error);
      alert("Failed to fetch messages");
    }
  }, [roomId, language, token]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  useEffect(() => {
    if (!roomId || !token) return;

    const socketUrl = `ws://localhost:8002/ws/chat/${roomId}/?token=${token}`;
    ws.current = new WebSocket(socketUrl);

    ws.current.onopen = () => {
      console.log("[WebSocket] Connected to", socketUrl);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("[WebSocket] Received:", data);

      if (data.type === "chat_message") {
        setMessages((prev) => [
          ...prev,
          {
            id: data.message_id || Date.now(),
            original_content: data.message,
            translated_content: null,
            sender: { username: data.username },
          },
        ]);
      } else if (data.type === "translation_update" && data.message_id) {
        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === data.message_id
              ? { ...msg, translated_content: data.message }
              : msg
          )
        );
      }
    };

    ws.current.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
    };

    ws.current.onclose = () => {
      console.log("[WebSocket] Closed");
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, [roomId, token]);

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

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    try {
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

  const handleSendMessage = (event) => {
    event.preventDefault();

    if (!newMessage.trim()) return;

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const payload = JSON.stringify({ message: newMessage });
      console.log("[WebSocket] Sending:", payload);
      ws.current.send(payload);
      setNewMessage("");
    } else {
      console.warn("[WebSocket] Not connected.");
      alert("Message not sent: WebSocket connection is not open.");
    }
  };

  const languages = [
    "original",
    "en",
    "es",
    "fr",
    "de",
    "da",
    "it",
    "ru",
    "zh",
    "ar",
    "ja",
  ];

  const getUserColor = (username) => {
    if (!username) return "#6c757d";
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
                <p style={{ margin: 0 }}>
                  {msg.translated_content || msg.original_content}
                </p>
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
