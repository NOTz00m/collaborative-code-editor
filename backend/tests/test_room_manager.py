"""
Unit tests for room management.
"""
import pytest
from room_manager import RoomManager, Room, User
import time


class TestUser:
    """Test cases for User class."""
    
    def test_user_creation(self):
        """Test creating a user."""
        user = User(
            user_id='user1',
            username='Alice',
            color='#FF0000'
        )
        
        assert user.user_id == 'user1'
        assert user.username == 'Alice'
        assert user.color == '#FF0000'
        assert user.cursor_position == 0
    
    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(
            user_id='user1',
            username='Bob',
            color='#00FF00',
            cursor_position=10
        )
        
        data = user.to_dict()
        assert data['userId'] == 'user1'
        assert data['username'] == 'Bob'
        assert data['color'] == '#00FF00'
        assert data['cursorPosition'] == 10


class TestRoom:
    """Test cases for Room class."""
    
    def test_room_creation(self):
        """Test creating a room."""
        room = Room(room_id='room1', language='python')
        
        assert room.room_id == 'room1'
        assert room.language == 'python'
        assert len(room.users) == 0
        assert room.crdt is not None
    
    def test_add_user(self):
        """Test adding a user to a room."""
        room = Room(room_id='room1')
        user = User(user_id='user1', username='Alice', color='#FF0000')
        
        room.add_user(user)
        assert len(room.users) == 1
        assert room.get_user('user1') == user
    
    def test_remove_user(self):
        """Test removing a user from a room."""
        room = Room(room_id='room1')
        user = User(user_id='user1', username='Alice', color='#FF0000')
        
        room.add_user(user)
        removed_user = room.remove_user('user1')
        
        assert removed_user == user
        assert len(room.users) == 0
        assert room.get_user('user1') is None
    
    def test_update_user_cursor(self):
        """Test updating user cursor position."""
        room = Room(room_id='room1')
        user = User(user_id='user1', username='Alice', color='#FF0000')
        room.add_user(user)
        
        success = room.update_user_cursor('user1', 15, 10, 20)
        assert success is True
        
        updated_user = room.get_user('user1')
        assert updated_user.cursor_position == 15
        assert updated_user.selection_start == 10
        assert updated_user.selection_end == 20
    
    def test_get_active_users(self):
        """Test getting active users."""
        room = Room(room_id='room1')
        
        # Add active user
        active_user = User(user_id='user1', username='Alice', color='#FF0000')
        room.add_user(active_user)
        
        # Add inactive user
        inactive_user = User(user_id='user2', username='Bob', color='#00FF00')
        inactive_user.last_active = time.time() - 400  # 400 seconds ago
        room.add_user(inactive_user)
        
        active_users = room.get_active_users()
        assert len(active_users) == 1
        assert active_users[0].user_id == 'user1'
    
    def test_room_to_dict(self):
        """Test converting room to dictionary."""
        room = Room(room_id='room1', language='javascript')
        user = User(user_id='user1', username='Alice', color='#FF0000')
        room.add_user(user)
        
        data = room.to_dict()
        assert data['roomId'] == 'room1'
        assert data['language'] == 'javascript'
        assert len(data['users']) == 1
        assert 'document' in data


class TestRoomManager:
    """Test cases for RoomManager class."""
    
    def test_create_room(self):
        """Test creating a room."""
        manager = RoomManager()
        room = manager.create_room(language='python')
        
        assert room is not None
        assert room.room_id is not None
        assert manager.room_exists(room.room_id)
    
    def test_get_room(self):
        """Test getting a room by ID."""
        manager = RoomManager()
        room = manager.create_room()
        
        retrieved_room = manager.get_room(room.room_id)
        assert retrieved_room == room
    
    def test_delete_room(self):
        """Test deleting a room."""
        manager = RoomManager()
        room = manager.create_room()
        
        success = manager.delete_room(room.room_id)
        assert success is True
        assert not manager.room_exists(room.room_id)
    
    def test_room_exists(self):
        """Test checking if a room exists."""
        manager = RoomManager()
        room = manager.create_room()
        
        assert manager.room_exists(room.room_id)
        assert not manager.room_exists('nonexistent')
    
    def test_get_all_rooms(self):
        """Test getting all rooms."""
        manager = RoomManager()
        room1 = manager.create_room(language='python')
        room2 = manager.create_room(language='javascript')
        
        all_rooms = manager.get_all_rooms()
        assert len(all_rooms) == 2
        
        room_ids = [r['roomId'] for r in all_rooms]
        assert room1.room_id in room_ids
        assert room2.room_id in room_ids
    
    def test_cleanup_inactive_rooms(self):
        """Test cleaning up inactive rooms."""
        manager = RoomManager()
        
        # Create an old room
        room = manager.create_room()
        room.created_at = time.time() - (25 * 3600)  # 25 hours ago
        
        # Create a recent room
        recent_room = manager.create_room()
        
        cleaned = manager.cleanup_inactive_rooms(max_age_hours=24)
        
        assert cleaned == 1
        assert not manager.room_exists(room.room_id)
        assert manager.room_exists(recent_room.room_id)
    
    def test_unique_room_ids(self):
        """Test that generated room IDs are unique."""
        manager = RoomManager()
        room_ids = set()
        
        for _ in range(100):
            room = manager.create_room()
            assert room.room_id not in room_ids
            room_ids.add(room.room_id)
