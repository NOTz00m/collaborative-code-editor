# API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: Configure via environment variables

## Authentication
Currently, the API does not require authentication. In production, implement JWT-based authentication.

## REST API Endpoints

### Health Check

**GET /**

Check if the API is online.

**Response:**
```json
{
  "status": "online",
  "service": "Collaborative Code Editor",
  "version": "1.0.0"
}
```

### Rooms

#### Create Room

**POST /api/rooms**

Create a new collaborative editing room.

**Request Body:**
```json
{
  "language": "python"  // Optional, defaults to "python"
}
```

**Supported Languages:**
- python
- javascript
- typescript
- java
- cpp
- go

**Response:** `200 OK`
```json
{
  "room_id": "xK9mP2nQ",
  "user_count": 0,
  "language": "python"
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

#### Get Room Information

**GET /api/rooms/{room_id}**

Retrieve detailed information about a specific room.

**Path Parameters:**
- `room_id` (string) - Unique room identifier

**Response:** `200 OK`
```json
{
  "roomId": "xK9mP2nQ",
  "createdAt": 1698765432.123,
  "users": [
    {
      "userId": "Abc123Xyz",
      "username": "Alice",
      "color": "#FF6B6B",
      "cursorPosition": 42,
      "selectionStart": null,
      "selectionEnd": null,
      "lastActive": 1698765500.456
    }
  ],
  "document": {
    "documentId": "xK9mP2nQ",
    "content": "print('Hello, World!')",
    "version": 5
  },
  "language": "python"
}
```

**Error Responses:**
- `404 Not Found` - Room does not exist

#### List All Rooms

**GET /api/rooms**

Get a list of all active rooms.

**Response:** `200 OK`
```json
[
  {
    "roomId": "xK9mP2nQ",
    "userCount": 2,
    "activeUserCount": 2,
    "createdAt": 1698765432.123,
    "language": "python"
  },
  {
    "roomId": "pL4kM9nR",
    "userCount": 1,
    "activeUserCount": 0,
    "createdAt": 1698765100.789,
    "language": "javascript"
  }
]
```

#### Delete Room

**DELETE /api/rooms/{room_id}**

Delete a room and disconnect all users.

**Path Parameters:**
- `room_id` (string) - Unique room identifier

**Response:** `200 OK`
```json
{
  "status": "deleted",
  "room_id": "xK9mP2nQ"
}
```

**Error Responses:**
- `404 Not Found` - Room does not exist

## WebSocket API

### Connection

**Endpoint:** `ws://localhost:8000/ws/{room_id}`

**Query Parameters:**
- `username` (string) - Display name for the user (default: "Anonymous")

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/xK9mP2nQ?username=Alice');
```

### Message Types

#### Server → Client Messages

##### 1. Initialization

Sent immediately after connection is established.

```json
{
  "type": "init",
  "userId": "Abc123Xyz",
  "color": "#FF6B6B",
  "document": {
    "documentId": "xK9mP2nQ",
    "content": "print('Hello, World!')",
    "version": 5
  },
  "users": [
    {
      "userId": "Abc123Xyz",
      "username": "Alice",
      "color": "#FF6B6B",
      "cursorPosition": 0,
      "selectionStart": null,
      "selectionEnd": null,
      "lastActive": 1698765500.456
    }
  ]
}
```

##### 2. Operation

Broadcast when another user makes an edit.

```json
{
  "type": "operation",
  "operation": {
    "type": "insert",
    "position": 10,
    "content": "hello",
    "clientId": "Xyz789Abc",
    "timestamp": 1698765500.789,
    "version": 6
  },
  "userId": "Xyz789Abc",
  "timestamp": "2023-10-25T12:30:00.789Z"
}
```

**Operation Types:**
- `insert` - Insert text at position
- `delete` - Delete text at position

##### 3. Cursor Update

Broadcast when another user moves their cursor or makes a selection.

```json
{
  "type": "cursor",
  "userId": "Xyz789Abc",
  "position": 15,
  "selectionStart": 10,
  "selectionEnd": 20,
  "timestamp": "2023-10-25T12:30:00.789Z"
}
```

##### 4. User Joined

Broadcast when a new user joins the room.

```json
{
  "type": "user_joined",
  "user": {
    "userId": "Def456Ghi",
    "username": "Bob",
    "color": "#4ECDC4",
    "cursorPosition": 0,
    "selectionStart": null,
    "selectionEnd": null,
    "lastActive": 1698765600.123
  },
  "timestamp": "2023-10-25T12:30:00.123Z"
}
```

##### 5. User Left

Broadcast when a user disconnects.

```json
{
  "type": "user_left",
  "userId": "Xyz789Abc",
  "username": "Alice",
  "timestamp": "2023-10-25T12:35:00.456Z"
}
```

##### 6. Pong

Response to ping (heartbeat).

```json
{
  "type": "pong"
}
```

#### Client → Server Messages

##### 1. Edit Operation

Send when making a change to the document.

```json
{
  "type": "operation",
  "operation": {
    "type": "insert",
    "position": 10,
    "content": "hello"
  }
}
```

**Operation Fields:**
- `type` (string) - "insert" or "delete"
- `position` (number) - Character offset in document
- `content` (string) - Text to insert or delete

##### 2. Cursor Update

Send when cursor position or selection changes.

```json
{
  "type": "cursor",
  "position": 15,
  "selectionStart": 10,
  "selectionEnd": 20
}
```

**Fields:**
- `position` (number) - Current cursor position
- `selectionStart` (number|null) - Selection start position
- `selectionEnd` (number|null) - Selection end position

##### 3. Ping (Heartbeat)

Send periodically to keep connection alive.

```json
{
  "type": "ping"
}
```

## Error Handling

### WebSocket Errors

**Connection Errors:**
- Code 4004: Room not found
- Code 1006: Abnormal closure (network issue)

**Reconnection Strategy:**
- Automatic reconnection with exponential backoff
- Maximum 5 reconnection attempts
- 2-second delay between attempts

### HTTP Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `404 Not Found` - Resource does not exist
- `500 Internal Server Error` - Server error

## Rate Limiting

Currently not implemented. For production:

- Implement rate limiting on REST endpoints
- Limit WebSocket message frequency
- Implement connection limits per IP

## CORS Configuration

Default allowed origins:
- http://localhost:3000
- http://localhost:5173

Configure via `CORS_ORIGINS` environment variable.

## Redis Integration

The backend uses Redis for:

1. **Pub/Sub Messaging** - Broadcast operations across server instances
2. **Document Storage** - Cache document content with 24-hour expiry

**Channels:**
- `room:{room_id}` - Room-specific messages

**Keys:**
- `document:{room_id}` - Document content (24h TTL)

## Example Usage

### JavaScript/TypeScript Client

```javascript
class CollaborativeEditor {
  constructor(roomId, username) {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/${roomId}?username=${username}`
    );
    
    this.ws.onopen = () => console.log('Connected');
    this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    this.ws.onerror = (error) => console.error('WebSocket error:', error);
    this.ws.onclose = () => this.reconnect();
  }
  
  handleMessage(message) {
    switch (message.type) {
      case 'init':
        this.initialize(message);
        break;
      case 'operation':
        this.applyOperation(message.operation);
        break;
      case 'cursor':
        this.updateCursor(message);
        break;
      case 'user_joined':
        this.addUser(message.user);
        break;
      case 'user_left':
        this.removeUser(message.userId);
        break;
    }
  }
  
  sendOperation(type, position, content) {
    this.ws.send(JSON.stringify({
      type: 'operation',
      operation: { type, position, content }
    }));
  }
  
  sendCursor(position, selectionStart = null, selectionEnd = null) {
    this.ws.send(JSON.stringify({
      type: 'cursor',
      position,
      selectionStart,
      selectionEnd
    }));
  }
}
```

### Python Client

```python
import asyncio
import websockets
import json

async def collaborate(room_id, username):
    uri = f"ws://localhost:8000/ws/{room_id}?username={username}"
    
    async with websockets.connect(uri) as websocket:
        # Receive init message
        init = json.loads(await websocket.recv())
        print(f"Connected as {init['userId']}")
        
        # Send an edit
        await websocket.send(json.dumps({
            "type": "operation",
            "operation": {
                "type": "insert",
                "position": 0,
                "content": "# Hello from Python\n"
            }
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")

asyncio.run(collaborate("xK9mP2nQ", "PythonBot"))
```

## Performance Considerations

1. **Message Size**: Maximum 1MB per WebSocket message
2. **Heartbeat**: 30-second interval for keep-alive
3. **Document Size**: No enforced limit (recommend < 1MB for performance)
4. **Active Users**: Tested with up to 50 concurrent users per room
5. **Latency**: Typical < 50ms for operation propagation in same data center

## Security Recommendations

For production deployment:

1. **Authentication**: Implement JWT-based auth
2. **Authorization**: Room access control
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Sanitize all inputs
5. **HTTPS/WSS**: Use encrypted connections
6. **CORS**: Restrict to your domain
7. **Content Security**: Validate document content
8. **Resource Limits**: Limit document and room sizes
