import React, { useState, useEffect } from "react";
import { Button, Container, ListGroup, Modal, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

const ChatRooms = ({ token }) => {
  const [chatRooms, setChatRooms] = useState([]);
  const [show, setShow] = useState(false);
  const [roomName, setRoomName] = useState("");
  const [members, setMembers] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchChatRooms = async () => {
      const response = await fetch("http://localhost:8002/api/chat/rooms/", {
        headers: { Authorization: `Token ${token}` },
      });
      const data = await response.json();
      setChatRooms(data);
    };
    fetchChatRooms();
  }, [token]);

  const handleCreateRoom = async () => {
    const memberUsernames = members.split(",").map((name) => name.trim());
    try {
      const response = await fetch("http://localhost:8002/api/chat/rooms/", {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: roomName,
          members_usernames: memberUsernames,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to create room: ${response.statusText}`);
      }
      setShow(false);
      navigate("/"); // Adjust as necessary to refresh or redirect
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  };

  return (
    <Container>
      <Button onClick={() => setShow(true)}>Create Chat Room</Button>
      <Modal show={show} onHide={() => setShow(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create a New Chat Room</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Room Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter room name"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Add Members (comma separated)</Form.Label>
              <Form.Control
                type="text"
                placeholder="Username1, Username2"
                value={members}
                onChange={(e) => setMembers(e.target.value)}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleCreateRoom}>
            Create Room
          </Button>
        </Modal.Footer>
      </Modal>
      <ListGroup>
        {chatRooms.map((room) => (
          <ListGroup.Item
            key={room.id}
            action
            onClick={() => navigate(`/chat-rooms/${room.id}/messages`)}
          >
            {room.name}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
};

export default ChatRooms;
