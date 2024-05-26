import React, { useState, useEffect } from "react"; // Ensure useEffect is imported
import { Route, Routes, Navigate } from "react-router-dom";
import Login from "./components/Login";
import ChatRooms from "./components/ChatRooms";
import AddMembers from "./components/AddMembers";
import Registration from "./components/Registration";
import Messages from "./components/Message";
import { Container, Navbar, Nav } from "react-bootstrap";

const App = () => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [currentRoomId, setCurrentRoomId] = useState("");

  useEffect(() => {
    // You can add more logic here if you need to validate the token
  }, []);

  const handleLogin = (newToken) => {
    setToken(newToken);
    localStorage.setItem("token", newToken);
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
                <Messages token={token} roomId={currentRoomId} />
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
