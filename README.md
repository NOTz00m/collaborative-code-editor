# Collaborative Code Editor

A production-ready real-time collaborative code editor built with FastAPI, React, and Monaco Editor. Multiple users can edit the same document simultaneously with conflict-free synchronization using CRDT (Conflict-free Replicated Data Types).

## Features

- Real-time collaborative editing with zero conflicts
- Monaco Editor integration with syntax highlighting for multiple languages
- WebSocket-based communication for instant updates
- User presence tracking with colored cursors and selections
- CRDT-based conflict resolution using Operational Transformation
- Redis pub/sub for horizontal scalability across multiple server instances
- Automatic reconnection handling and graceful degradation
- Clean, modern UI with dark theme
- Room-based sessions with unique IDs
- Toast notifications for user events

## Architecture

```
┌─────────────┐         WebSocket          ┌─────────────┐
│   Frontend  │◄──────────────────────────►│   Backend   │
│   (React)   │         REST API           │  (FastAPI)  │
└─────────────┘                            └──────┬──────┘
      │                                           │
      │                                           │
      │                                    ┌──────▼──────┐
      │                                    │    Redis    │
      │                                    │  (Pub/Sub)  │
      │                                    └─────────────┘
      │                                           │
      └───────────────────────────────────────────┘
           Scalable multi-instance support
```

### Components

**Backend (Python/FastAPI)**
- FastAPI server with WebSocket support
- Room management system
- CRDT implementation for conflict-free editing
- Redis pub/sub for message broadcasting
- User presence and cursor tracking
- RESTful API for room operations

**Frontend (React)**
- Monaco Editor integration
- WebSocket client with auto-reconnect
- Real-time cursor rendering
- User presence sidebar
- Room creation/joining interface

**Infrastructure**
- Redis for pub/sub messaging
- Docker Compose for deployment
- Pytest for backend testing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd collaborative-code-editor
```

2. Start all services:
```bash
docker-compose up
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Start Redis (required):
```bash
docker run -p 6379:6379 redis:7-alpine
```

Run the backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Usage

### Creating a Room

1. Open the application
2. Enter your username
3. Select a programming language
4. Click "Create Room"
5. Share the room ID with collaborators

### Joining a Room

1. Get the room ID from someone
2. Enter the room ID and your username
3. Click "Join Room"
4. Start collaborating

### Collaborative Editing

- Your cursor and selections are visible to others in real-time
- Changes are synchronized instantly with conflict resolution
- Active users are shown in the sidebar with colored indicators
- Click the room ID to copy it to clipboard

## API Documentation

### REST Endpoints

#### Create Room
```
POST /api/rooms
Content-Type: application/json

{
  "language": "python"
}

Response:
{
  "room_id": "abc123",
  "user_count": 0,
  "language": "python"
}
```

#### Get Room
```
GET /api/rooms/{room_id}

Response:
{
  "roomId": "abc123",
  "createdAt": 1234567890,
  "users": [...],
  "document": {...},
  "language": "python"
}
```

#### List Rooms
```
GET /api/rooms

Response: [
  {
    "roomId": "abc123",
    "userCount": 2,
    "activeUserCount": 2,
    "createdAt": 1234567890,
    "language": "python"
  }
]
```

#### Delete Room
```
DELETE /api/rooms/{room_id}

Response:
{
  "status": "deleted",
  "room_id": "abc123"
}
```

### WebSocket Protocol

Connect to: `ws://localhost:8000/ws/{room_id}?username={username}`

#### Messages from Server

**Init Message** (on connection):
```json
{
  "type": "init",
  "userId": "user123",
  "color": "#FF6B6B",
  "document": {
    "documentId": "room123",
    "content": "...",
    "version": 5
  },
  "users": [...]
}
```

**Operation Message** (on edit):
```json
{
  "type": "operation",
  "operation": {
    "type": "insert",
    "position": 10,
    "content": "hello",
    "clientId": "user123"
  },
  "userId": "user123"
}
```

**Cursor Message**:
```json
{
  "type": "cursor",
  "userId": "user123",
  "position": 15,
  "selectionStart": 10,
  "selectionEnd": 20
}
```

**User Joined**:
```json
{
  "type": "user_joined",
  "user": {
    "userId": "user456",
    "username": "Alice",
    "color": "#4ECDC4"
  }
}
```

**User Left**:
```json
{
  "type": "user_left",
  "userId": "user456",
  "username": "Alice"
}
```

#### Messages to Server

**Edit Operation**:
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

**Cursor Update**:
```json
{
  "type": "cursor",
  "position": 15,
  "selectionStart": 10,
  "selectionEnd": 20
}
```

**Heartbeat**:
```json
{
  "type": "ping"
}
```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

Test coverage includes:
- CRDT operations and transformations
- Room management
- WebSocket connections
- REST API endpoints

### Running Specific Tests

```bash
# Test CRDT only
pytest tests/test_crdt.py -v

# Test room management
pytest tests/test_room_manager.py -v

# Test WebSocket
pytest tests/test_websocket.py -v
```

## CRDT Implementation

The application uses a simplified Operational Transformation (OT) approach:

1. Each client maintains a version counter
2. Operations are timestamped and assigned to clients
3. Concurrent operations are transformed based on position adjustments
4. Insert operations adjust positions of subsequent operations
5. Delete operations reduce positions accordingly

This ensures that all clients converge to the same document state regardless of operation order.

## Configuration

### Environment Variables

**Backend** (.env in backend directory):
```
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000"]
```

**Frontend** (.env in frontend directory):
```
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Deployment

### Production Considerations

1. **Security**:
   - Set a strong SECRET_KEY
   - Configure CORS_ORIGINS to your domain
   - Use HTTPS/WSS in production
   - Implement rate limiting
   - Add authentication/authorization

2. **Scalability**:
   - Redis enables multiple backend instances
   - Use a load balancer for WebSocket connections
   - Configure Redis persistence
   - Monitor resource usage

3. **Performance**:
   - Enable Redis persistence (AOF)
   - Configure appropriate WebSocket message size limits
   - Implement document size limits
   - Add cleanup jobs for inactive rooms

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Run in production mode
docker-compose up -d
```

## Troubleshooting

### WebSocket Connection Fails

- Check that the backend is running
- Verify CORS settings in backend config
- Ensure Redis is running
- Check firewall settings

### Edits Not Syncing

- Verify WebSocket connection status (indicator in header)
- Check browser console for errors
- Ensure multiple users are in the same room
- Restart the backend service

### Redis Connection Issues

- Ensure Redis is running: `docker ps`
- Check Redis logs: `docker logs <redis-container>`
- Verify REDIS_HOST and REDIS_PORT settings

## Contributing

Contributions are welcome. Please ensure all tests pass before submitting pull requests.

```bash
# Run backend tests
cd backend && pytest

# Run frontend linting
cd frontend && npm run lint
```
