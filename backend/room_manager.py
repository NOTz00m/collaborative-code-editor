"""
Room management system for collaborative editing sessions.
Handles room creation, user management, and document state.
"""
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field
import secrets
import time
from crdt import CRDT


@dataclass
class User:
    """Represents a user in a room."""
    user_id: str
    username: str
    color: str
    cursor_position: int = 0
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    last_active: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'userId': self.user_id,
            'username': self.username,
            'color': self.color,
            'cursorPosition': self.cursor_position,
            'selectionStart': self.selection_start,
            'selectionEnd': self.selection_end,
            'lastActive': self.last_active
        }


@dataclass
class Room:
    """Represents a collaborative editing room."""
    room_id: str
    created_at: float = field(default_factory=time.time)
    users: Dict[str, User] = field(default_factory=dict)
    crdt: CRDT = field(init=False)
    language: str = "python"
    
    def __post_init__(self):
        """Initialize CRDT for this room."""
        self.crdt = CRDT(self.room_id)
    
    def add_user(self, user: User) -> None:
        """Add a user to the room."""
        self.users[user.user_id] = user
    
    def remove_user(self, user_id: str) -> Optional[User]:
        """Remove a user from the room."""
        return self.users.pop(user_id, None)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(user_id)
    
    def update_user_cursor(
        self, 
        user_id: str, 
        position: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None
    ) -> bool:
        """Update user's cursor position and selection."""
        user = self.users.get(user_id)
        if user:
            user.cursor_position = position
            user.selection_start = selection_start
            user.selection_end = selection_end
            user.last_active = time.time()
            return True
        return False
    
    def get_active_users(self) -> List[User]:
        """Get list of active users (active in last 5 minutes)."""
        current_time = time.time()
        return [
            user for user in self.users.values()
            if current_time - user.last_active < 300  # 5 minutes
        ]
    
    def to_dict(self) -> dict:
        """Convert room to dictionary."""
        return {
            'roomId': self.room_id,
            'createdAt': self.created_at,
            'users': [user.to_dict() for user in self.users.values()],
            'document': self.crdt.get_state(),
            'language': self.language
        }


class RoomManager:
    """Manages all collaborative editing rooms."""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
    
    def create_room(self, language: str = "python") -> Room:
        """Create a new room with a unique ID."""
        room_id = self._generate_room_id()
        room = Room(room_id=room_id, language=language)
        self.rooms[room_id] = room
        return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False
    
    def room_exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        return room_id in self.rooms
    
    def cleanup_inactive_rooms(self, max_age_hours: int = 24) -> int:
        """
        Remove rooms that have been inactive for too long.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of rooms cleaned up
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        inactive_rooms = [
            room_id for room_id, room in self.rooms.items()
            if current_time - room.created_at > max_age_seconds
            and len(room.get_active_users()) == 0
        ]
        
        for room_id in inactive_rooms:
            del self.rooms[room_id]
        
        return len(inactive_rooms)
    
    def _generate_room_id(self) -> str:
        """Generate a unique room ID."""
        while True:
            room_id = secrets.token_urlsafe(8)
            if room_id not in self.rooms:
                return room_id
    
    def get_all_rooms(self) -> List[dict]:
        """Get information about all rooms."""
        return [
            {
                'roomId': room.room_id,
                'userCount': len(room.users),
                'activeUserCount': len(room.get_active_users()),
                'createdAt': room.created_at,
                'language': room.language
            }
            for room in self.rooms.values()
        ]


# Global room manager instance
room_manager = RoomManager()
