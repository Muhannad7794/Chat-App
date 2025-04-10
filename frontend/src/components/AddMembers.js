// AddMembers.js
import React, { useState, useEffect } from "react";
import { Button, Container, Form } from "react-bootstrap";
import { useParams } from "react-router-dom";

const AddMembers = ({ token }) => {
  const { roomId } = useParams();
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");

  useEffect(() => {
    const fetchUsers = async () => {
      const response = await fetch("http://localhost:8001/api/users/", {
        headers: { Authorization: `Token ${token}` },
      });
      const data = await response.json();
      if (response.ok) {
        setUsers(data);
      } else {
        alert("Failed to fetch users");
      }
    };

    fetchUsers();
  }, [token]);

  const handleAddMember = async (event) => {
    event.preventDefault();
    const response = await fetch(
      `http://localhost:8002/api/chat/rooms/${roomId}/add-member/`,
      {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: selectedUser }),
      }
    );
    if (response.ok) {
      alert("Member added successfully!");
    } else {
      alert("Failed to add member");
    }
  };

  return (
    <Container>
      <h2>Add Members to Chat Room {roomId}</h2>
      <Form onSubmit={handleAddMember}>
        <Form.Group controlId="formUserSelect">
          <Form.Label>Select User</Form.Label>
          <Form.Control
            as="select"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
          >
            <option value="">-- Select a user --</option>
            {users.map((user) => (
              <option key={user.id} value={user.username}>
                {user.username}
              </option>
            ))}
          </Form.Control>
        </Form.Group>
        <Button type="submit" variant="primary">
          Add Member
        </Button>
      </Form>
    </Container>
  );
};

export default AddMembers;
