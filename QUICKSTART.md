# Quick Start Guide

## Running with Docker (Recommended)

This is the fastest way to get started.

### 1. Prerequisites
- Docker Desktop installed and running
- Git (to clone the repository)

### 2. Start the Application

```bash
# Clone or navigate to the project directory
cd collaborative-code-editor

# Start all services (Redis, Backend, Frontend)
docker-compose up
```

Wait for all services to start (about 30-60 seconds).

### 3. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Create Your First Room

1. Open http://localhost:3000
2. Enter your username (e.g., "Alice")
3. Select a programming language
4. Click "Create Room"
5. Copy the room ID from the header
6. Share it with friends to collaborate

### 5. Join a Room

1. Open http://localhost:3000 in another browser/tab
2. Enter the room ID
3. Enter a different username (e.g., "Bob")
4. Click "Join Room"
5. Start coding together!

## Local Development Setup

For development with hot-reload:

### 1. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# Start the frontend
npm run dev
```

Frontend will be available at http://localhost:3000

## Testing

### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Test Coverage

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

## Common Issues

### Port Already in Use

If ports 3000, 8000, or 6379 are already in use:

**Option 1**: Stop the conflicting service
**Option 2**: Change ports in docker-compose.yml and .env files

### Docker Issues

```bash
# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up --build
```

### Backend Not Connecting to Redis

1. Check Redis is running: `docker ps`
2. Verify Redis connection: `redis-cli ping` (should return PONG)
3. Check REDIS_HOST in backend/.env (should be "localhost" for local dev, "redis" for Docker)

### WebSocket Connection Failed

1. Ensure backend is running on port 8000
2. Check browser console for errors
3. Verify VITE_WS_URL in frontend/.env matches backend URL

## Next Steps

1. Read the full [README.md](README.md) for detailed information
2. Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API reference
3. Explore the code in `backend/` and `frontend/src/`
4. Run tests to understand the system better
5. Try making changes and see hot-reload in action

## Production Deployment

For production:

1. Set strong SECRET_KEY in backend/.env
2. Configure proper CORS_ORIGINS
3. Use HTTPS/WSS
4. Set up Redis persistence
5. Configure a reverse proxy (nginx/traefik)
6. Enable logging and monitoring
7. Implement rate limiting
8. Add authentication

See README.md for detailed production deployment guide.

## Need Help?

- Check the troubleshooting section in README.md
- Review API documentation
- Check backend logs: `docker-compose logs backend`
- Check frontend console in browser DevTools
