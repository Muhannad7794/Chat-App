// ChatRooms.js
import React, { useState, useEffect } from "react";
import { Button, Container, ListGroup, Modal, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const ChatRooms = ({ token, setCurrentRoomId, currentUsername }) => {
  const [chatRooms, setChatRooms] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [roomName, setRoomName] = useState("");
  const [members, setMembers] = useState("");

  // Rename Modal State
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameRoomName, setRenameRoomName] = useState("");
  const [roomToRename, setRoomToRename] = useState(null);

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [roomToDelete, setRoomToDelete] = useState(null);

  // Manage Members Modal State (for admin)
  const [showManageMembersModal, setShowManageMembersModal] = useState(false);
  const [membersList, setMembersList] = useState([]);

  const navigate = useNavigate();

  const fetchChatRooms = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8002/api/chat/rooms/",
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setChatRooms(response.data);
    } catch (error) {
      console.error("Failed to fetch chat rooms:", error);
    }
  };

  useEffect(() => {
    fetchChatRooms();
  }, [token]);

  // Create Room Handler
  const handleCreateRoom = async () => {
    const memberUsernames = members.split(",").map((name) => name.trim());
    try {
      await axios.post(
        "http://localhost:8002/api/chat/rooms/",
        {
          name: roomName,
          members_usernames: memberUsernames,
        },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      alert("Chat room created successfully!");
      setShowCreateModal(false);
      fetchChatRooms();
      navigate("/chat-rooms");
    } catch (error) {
      console.error(error);
      alert("Failed to create room: " + error.message);
    }
  };

  // Rename Room Handler (Admin-only)
  const handleRenameRoom = async () => {
    if (!roomToRename) return;
    try {
      await axios.put(
        `http://localhost:8002/api/chat/rooms/${roomToRename.id}/`,
        { name: renameRoomName },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      alert("Room renamed successfully!");
      setShowRenameModal(false);
      fetchChatRooms();
    } catch (error) {
      console.error("Rename failed:", error);
      alert("Failed to rename room.");
    }
  };

  // Delete Room Handler (Admin-only)
  const handleDeleteRoom = async () => {
    if (!roomToDelete) return;
    try {
      await axios.delete(
        `http://localhost:8002/api/chat/rooms/${roomToDelete.id}/`,
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      alert("Room deleted successfully!");
      setShowDeleteModal(false);
      fetchChatRooms();
    } catch (error) {
      console.error("Delete failed:", error);
      alert("Failed to delete room.");
    }
  };

  // Leave Room Handler (Non-admin)
  const handleLeaveRoom = async (room) => {
    try {
      await axios.post(
        `http://localhost:8002/api/chat/rooms/${room.id}/leave/`,
        {},
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      alert("You have left the room.");
      fetchChatRooms();
    } catch (error) {
      console.error("Leave room failed:", error);
      alert("Failed to leave room.");
    }
  };

  // Fetch Room Members for Manage Members Modal
  const fetchRoomMembers = async (roomId) => {
    try {
      const response = await axios.get(
        `http://localhost:8002/api/chat/rooms/${roomId}/`,
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      // Assuming the room object has a 'members' property that is an array of member objects.
      setMembersList(response.data.members || []);
    } catch (error) {
      console.error("Failed to fetch room members:", error);
    }
  };

  // Remove Member Handler (Admin-only)
  const handleRemoveMember = async (roomId, memberId) => {
    try {
      await axios.post(
        `http://localhost:8002/api/chat/rooms/${roomId}/remove-member/`,
        { user_id: memberId },
        {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      alert("Member removed successfully!");
      fetchRoomMembers(roomId);
    } catch (error) {
      console.error("Failed to remove member:", error);
      alert("Failed to remove member.");
    }
  };

  // Open Manage Members Modal (Admin-only)
  const openManageMembersModal = async (room) => {
    await fetchRoomMembers(room.id);
    setRoomToRename(room); // Reuse roomToRename for managing members context
    setShowManageMembersModal(true);
  };

  return (
    <Container>
      <Button onClick={() => setShowCreateModal(true)}>Create Chat Room</Button>

      {/* Create Room Modal */}
      <Modal show={showCreateModal} onHide={() => setShowCreateModal(false)}>
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
              <Form.Label>Add Members (comma separated usernames)</Form.Label>
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
          <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
            Close
          </Button>
          <Button variant="primary" onClick={handleCreateRoom}>
            Create Room
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Rename Modal */}
      <Modal show={showRenameModal} onHide={() => setShowRenameModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Rename Chat Room</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>New Room Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter new room name"
              value={renameRoomName}
              onChange={(e) => setRenameRoomName(e.target.value)}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRenameModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleRenameRoom}>
            Rename
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete Chat Room</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete the room "{roomToDelete?.name}"? This
          action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDeleteRoom}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Manage Members Modal */}
      <Modal
        show={showManageMembersModal}
        onHide={() => setShowManageMembersModal(false)}
      >
        <Modal.Header closeButton>
          <Modal.Title>Manage Members for "{roomToRename?.name}"</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {membersList && membersList.length > 0 ? (
            <ListGroup>
              {membersList.map((member) => (
                <ListGroup.Item
                  key={member.id}
                  className="d-flex justify-content-between align-items-center"
                >
                  {member.username}
                  {member.username !== currentUsername && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() =>
                        handleRemoveMember(roomToRename.id, member.id)
                      }
                    >
                      Remove
                    </Button>
                  )}
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            <p>No members found.</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => setShowManageMembersModal(false)}
          >
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      <ListGroup className="mt-3">
        {chatRooms.map((room) => (
          <ListGroup.Item key={room.id}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div
                style={{ cursor: "pointer" }}
                onClick={() => {
                  setCurrentRoomId(room.id);
                  navigate(`/chat-rooms/${room.id}/messages`);
                }}
              >
                {room.name}
              </div>
              <div>
                {room.admin === currentUsername ? (
                  <>
                    <Button
                      variant="info"
                      size="sm"
                      onClick={() => {
                        setRoomToRename(room);
                        setRenameRoomName(room.name);
                        setShowRenameModal(true);
                      }}
                      style={{ marginRight: "5px" }}
                    >
                      Rename
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        setRoomToDelete(room);
                        setShowDeleteModal(true);
                      }}
                      style={{ marginRight: "5px" }}
                    >
                      Delete
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openManageMembersModal(room)}
                    >
                      Manage Members
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="warning"
                    size="sm"
                    onClick={() => handleLeaveRoom(room)}
                  >
                    Leave
                  </Button>
                )}
              </div>
            </div>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Container>
  );
};

export default ChatRooms;
