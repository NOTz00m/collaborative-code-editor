"""
WebSocket connection manager for handling real-time communication.
"""
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """
    Manages WebSocket connections for collaborative editing.
    Handles message broadcasting and connection lifecycle.
    """
    
    def __init__(self):
        # Map of room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> user_id
        self.connection_users: Dict[WebSocket, str] = {}
        # Map of WebSocket -> room_id
        self.connection_rooms: Dict[WebSocket, str] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        room_id: str, 
        user_id: str
    ) -> None:
        """
        Accept a new WebSocket connection and add it to a room.
        
        Args:
            websocket: The WebSocket connection
            room_id: Room to join
            user_id: User identifier
        """
        await websocket.accept()
        
        # Add to room's connection set
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        
        # Track connection metadata
        self.connection_users[websocket] = user_id
        self.connection_rooms[websocket] = room_id
        
        print(f"User {user_id} connected to room {room_id}")
    
    def disconnect(self, websocket: WebSocket) -> Optional[tuple[str, str]]:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
            
        Returns:
            Tuple of (room_id, user_id) if connection existed
        """
        room_id = self.connection_rooms.pop(websocket, None)
        user_id = self.connection_users.pop(websocket, None)
        
        if room_id and room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            
            # Clean up empty rooms
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if room_id and user_id:
            print(f"User {user_id} disconnected from room {room_id}")
            return room_id, user_id
        
        return None
    
    async def send_personal_message(
        self, 
        message: dict, 
        websocket: WebSocket
    ) -> None:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast_to_room(
        self, 
        message: dict, 
        room_id: str,
        exclude: Optional[WebSocket] = None
    ) -> None:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            message: Message data
            room_id: Target room ID
            exclude: Optional WebSocket to exclude from broadcast
        """
        if room_id not in self.active_connections:
            return
        
        # Add timestamp to message
        message['timestamp'] = datetime.utcnow().isoformat()
        
        # Broadcast to all connections in room
        disconnected = []
        for connection in self.active_connections[room_id]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_all(self, message: dict) -> None:
        """
        Broadcast a message to all active connections.
        
        Args:
            message: Message data
        """
        for room_id in self.active_connections:
            await self.broadcast_to_room(message, room_id)
    
    def get_room_connection_count(self, room_id: str) -> int:
        """Get the number of active connections in a room."""
        return len(self.active_connections.get(room_id, set()))
    
    def get_user_id(self, websocket: WebSocket) -> Optional[str]:
        """Get the user ID for a WebSocket connection."""
        return self.connection_users.get(websocket)
    
    def get_room_id(self, websocket: WebSocket) -> Optional[str]:
        """Get the room ID for a WebSocket connection."""
        return self.connection_rooms.get(websocket)


# Global connection manager instance
connection_manager = ConnectionManager()
