"""
Main FastAPI application for collaborative code editor.
Handles HTTP endpoints and WebSocket connections.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import secrets

from config import settings
from room_manager import room_manager, User
from websocket_manager import connection_manager
from redis_service import redis_pubsub
from crdt import Operation

# Color palette for user cursors
USER_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", 
    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2",
    "#F8B739", "#52B788", "#E76F51", "#2A9D8F"
]

app = FastAPI(title="Collaborative Code Editor API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class CreateRoomRequest(BaseModel):
    language: Optional[str] = "python"


class JoinRoomRequest(BaseModel):
    room_id: str
    username: str


class RoomResponse(BaseModel):
    room_id: str
    user_count: int
    language: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    color: str


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await redis_pubsub.connect()
        # Start Redis listener as background task
        asyncio.create_task(redis_pubsub.listen())
        print("Application started successfully")
    except Exception as e:
        print(f"Warning: Redis connection failed: {e}")
        print("Continuing without Redis (single-instance mode)")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await redis_pubsub.disconnect()
    print("Application shutdown complete")


# REST API Endpoints
@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "service": "Collaborative Code Editor",
        "version": "1.0.0"
    }


@app.post("/api/rooms", response_model=RoomResponse)
async def create_room(request: CreateRoomRequest):
    """
    Create a new collaborative editing room.
    
    Args:
        request: Room creation request with optional language
        
    Returns:
        Room information including unique room ID
    """
    room = room_manager.create_room(language=request.language)
    
    # Initialize empty document in Redis
    await redis_pubsub.store_document(room.room_id, "")
    
    return RoomResponse(
        room_id=room.room_id,
        user_count=0,
        language=room.language
    )


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """
    Get information about a specific room.
    
    Args:
        room_id: The room identifier
        
    Returns:
        Room details including users and document state
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return room.to_dict()


@app.get("/api/rooms")
async def list_rooms():
    """
    List all active rooms.
    
    Returns:
        List of room information
    """
    return room_manager.get_all_rooms()


@app.delete("/api/rooms/{room_id}")
async def delete_room(room_id: str):
    """
    Delete a room.
    
    Args:
        room_id: The room identifier
        
    Returns:
        Success status
    """
    success = room_manager.delete_room(room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {"status": "deleted", "room_id": room_id}


# WebSocket endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str = "Anonymous"):
    """
    WebSocket endpoint for real-time collaboration.
    
    Args:
        websocket: WebSocket connection
        room_id: Room to join
        username: User's display name
    """
    # Check if room exists
    room = room_manager.get_room(room_id)
    if not room:
        await websocket.close(code=4004, reason="Room not found")
        return
    
    # Generate user ID and assign color
    user_id = secrets.token_urlsafe(8)
    color = USER_COLORS[len(room.users) % len(USER_COLORS)]
    
    # Create user and add to room
    user = User(user_id=user_id, username=username, color=color)
    room.add_user(user)
    
    # Connect WebSocket
    await connection_manager.connect(websocket, room_id, user_id)
    
    try:
        # Send initial state to new user
        await websocket.send_json({
            'type': 'init',
            'userId': user_id,
            'color': color,
            'document': room.crdt.get_state(),
            'users': [u.to_dict() for u in room.users.values()]
        })
        
        # Notify other users
        await connection_manager.broadcast_to_room(
            {
                'type': 'user_joined',
                'user': user.to_dict()
            },
            room_id,
            exclude=websocket
        )
        
        # Publish to Redis for other server instances
        await redis_pubsub.publish(f"room:{room_id}", {
            'type': 'user_joined',
            'user': user.to_dict()
        })
        
        # Message handling loop
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(websocket, room_id, user_id, data)
            
    except WebSocketDisconnect:
        # Handle disconnection
        await handle_disconnect(websocket, room_id, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await handle_disconnect(websocket, room_id, user_id)


async def handle_websocket_message(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    data: dict
):
    """
    Handle incoming WebSocket messages.
    
    Args:
        websocket: WebSocket connection
        room_id: Room identifier
        user_id: User identifier
        data: Message data
    """
    room = room_manager.get_room(room_id)
    if not room:
        return
    
    message_type = data.get('type')
    
    if message_type == 'operation':
        # Handle collaborative edit operation
        operation = Operation.from_dict(data.get('operation', {}))
        operation.client_id = user_id
        
        # Apply operation to CRDT
        success = room.crdt.apply_operation(operation)
        
        if success:
            # Broadcast operation to other users
            await connection_manager.broadcast_to_room(
                {
                    'type': 'operation',
                    'operation': operation.to_dict(),
                    'userId': user_id
                },
                room_id,
                exclude=websocket
            )
            
            # Publish to Redis
            await redis_pubsub.publish(f"room:{room_id}", {
                'type': 'operation',
                'operation': operation.to_dict(),
                'userId': user_id
            })
            
            # Store updated document
            await redis_pubsub.store_document(room_id, room.crdt.content)
    
    elif message_type == 'cursor':
        # Handle cursor position update
        position = data.get('position', 0)
        selection_start = data.get('selectionStart')
        selection_end = data.get('selectionEnd')
        
        room.update_user_cursor(user_id, position, selection_start, selection_end)
        
        # Broadcast cursor position
        await connection_manager.broadcast_to_room(
            {
                'type': 'cursor',
                'userId': user_id,
                'position': position,
                'selectionStart': selection_start,
                'selectionEnd': selection_end
            },
            room_id,
            exclude=websocket
        )
    
    elif message_type == 'ping':
        # Respond to heartbeat
        await websocket.send_json({'type': 'pong'})


async def handle_disconnect(websocket: WebSocket, room_id: str, user_id: str):
    """
    Handle WebSocket disconnection.
    
    Args:
        websocket: WebSocket connection
        room_id: Room identifier
        user_id: User identifier
    """
    connection_manager.disconnect(websocket)
    
    room = room_manager.get_room(room_id)
    if room:
        user = room.remove_user(user_id)
        
        if user:
            # Notify other users
            await connection_manager.broadcast_to_room(
                {
                    'type': 'user_left',
                    'userId': user_id,
                    'username': user.username
                },
                room_id
            )
            
            # Publish to Redis
            await redis_pubsub.publish(f"room:{room_id}", {
                'type': 'user_left',
                'userId': user_id,
                'username': user.username
            })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
