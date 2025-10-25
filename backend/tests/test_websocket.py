"""
Integration tests for WebSocket endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import json
import asyncio

from main import app
from room_manager import room_manager


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up rooms between tests."""
    yield
    room_manager.rooms.clear()


class TestHTTPEndpoints:
    """Test REST API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'online'
    
    def test_create_room(self, client):
        """Test creating a room."""
        response = client.post(
            "/api/rooms",
            json={"language": "python"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'room_id' in data
        assert data['language'] == 'python'
    
    def test_get_room(self, client):
        """Test getting room information."""
        # Create a room first
        create_response = client.post(
            "/api/rooms",
            json={"language": "javascript"}
        )
        room_id = create_response.json()['room_id']
        
        # Get the room
        response = client.get(f"/api/rooms/{room_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['roomId'] == room_id
    
    def test_get_nonexistent_room(self, client):
        """Test getting a room that doesn't exist."""
        response = client.get("/api/rooms/nonexistent")
        assert response.status_code == 404
    
    def test_list_rooms(self, client):
        """Test listing all rooms."""
        # Create some rooms
        client.post("/api/rooms", json={"language": "python"})
        client.post("/api/rooms", json={"language": "javascript"})
        
        response = client.get("/api/rooms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_delete_room(self, client):
        """Test deleting a room."""
        # Create a room
        create_response = client.post("/api/rooms", json={})
        room_id = create_response.json()['room_id']
        
        # Delete it
        response = client.delete(f"/api/rooms/{room_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/rooms/{room_id}")
        assert get_response.status_code == 404


class TestWebSocket:
    """Test WebSocket functionality."""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection to a room."""
        # Create a room
        create_response = client.post("/api/rooms", json={})
        room_id = create_response.json()['room_id']
        
        # Connect via WebSocket
        with client.websocket_connect(f"/ws/{room_id}?username=TestUser") as websocket:
            # Should receive init message
            data = websocket.receive_json()
            assert data['type'] == 'init'
            assert 'userId' in data
            assert 'color' in data
            assert data['document']['documentId'] == room_id
    
    def test_websocket_invalid_room(self, client):
        """Test connecting to a non-existent room."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/nonexistent?username=TestUser"):
                pass
    
    def test_websocket_multiple_users(self, client):
        """Test multiple users connecting to the same room."""
        # Create a room
        create_response = client.post("/api/rooms", json={})
        room_id = create_response.json()['room_id']
        
        # Connect first user
        with client.websocket_connect(f"/ws/{room_id}?username=User1") as ws1:
            init1 = ws1.receive_json()
            assert init1['type'] == 'init'
            
            # Connect second user
            with client.websocket_connect(f"/ws/{room_id}?username=User2") as ws2:
                init2 = ws2.receive_json()
                assert init2['type'] == 'init'
                
                # First user should receive user_joined message
                joined = ws1.receive_json()
                assert joined['type'] == 'user_joined'
                assert joined['user']['username'] == 'User2'
    
    def test_websocket_ping_pong(self, client):
        """Test WebSocket heartbeat."""
        create_response = client.post("/api/rooms", json={})
        room_id = create_response.json()['room_id']
        
        with client.websocket_connect(f"/ws/{room_id}?username=TestUser") as websocket:
            # Skip init message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            response = websocket.receive_json()
            assert response['type'] == 'pong'
