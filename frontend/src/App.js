// src/App.js
import React, { useState, useEffect } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import Login from "./components/Login";
import ChatRooms from "./components/ChatRooms";
import AddMembers from "./components/AddMembers";
import Registration from "./components/Registration";
import Messages from "./components/Message";
import { Container, Navbar, Nav } from "react-bootstrap";

const App = () => {
  // Retrieve token and username from localStorage if available
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [username, setUsername] = useState(localStorage.getItem("username"));
  const [currentRoomId, setCurrentRoomId] = useState("");

  useEffect(() => {
    // Additional token validation logic can be added here if needed.
  }, []);

  // Modified handleLogin to receive both token and username
  const handleLogin = (newToken, newUsername) => {
    setToken(newToken);
    setUsername(newUsername);
    localStorage.setItem("token", newToken);
    localStorage.setItem("username", newUsername);
  };

  return (
    <div>
      <Navbar bg="light" expand="lg">
        <Navbar.Brand href="/">Chat App</Navbar.Brand>
        <Nav className="me-auto">
          <Nav.Link href="/login">Login</Nav.Link>
          <Nav.Link href="/register">Register</Nav.Link>
          <Nav.Link href="/chat-rooms">Chat Rooms</Nav.Link>
          {token && currentRoomId && (
            <Nav.Link href={`/chat-rooms/${currentRoomId}/messages`}>
              Messages
            </Nav.Link>
          )}
          {token && currentRoomId && (
            <Nav.Link href={`/add-members/${currentRoomId}`}>
              Add Members
            </Nav.Link>
          )}
        </Nav>
      </Navbar>
      <Container>
        <Routes>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="/register" element={<Registration />} />
          <Route
            path="/chat-rooms/:roomId/messages"
            element={
              token ? (
                <Messages
                  token={token}
                  currentUsername={username}
                  roomId={currentRoomId}
                />
              ) : (
                <Navigate replace to="/login" />
              )
            }
          />
          <Route
            path="/chat-rooms"
            element={
              token ? (
                <ChatRooms token={token} setCurrentRoomId={setCurrentRoomId} />
              ) : (
                <Navigate replace to="/login" />
              )
            }
          />
          <Route
            path="/add-members/:roomId"
            element={
              token ? (
                <AddMembers token={token} roomId={currentRoomId} />
              ) : (
                <Navigate replace to="/login" />
              )
            }
          />
          <Route path="/" element={<Navigate replace to="/login" />} />
        </Routes>
      </Container>
    </div>
  );
};

export default App;
