# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Docker not starting
**Symptoms:** `docker-compose up` fails immediately

**Solutions:**
1. Ensure Docker Desktop is running
2. Check Docker daemon status: `docker ps`
3. Restart Docker Desktop
4. On Windows, ensure WSL2 is installed and enabled

#### Port conflicts
**Symptoms:** "Port already in use" error

**Solutions:**
1. Check what's using the ports:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   netstat -ano | findstr :6379
   
   # Linux/Mac
   lsof -i :8000
   lsof -i :3000
   lsof -i :6379
   ```

2. Stop conflicting services or change ports in docker-compose.yml

3. Alternative ports in docker-compose.yml:
   ```yaml
   ports:
     - "8001:8000"  # Backend
     - "3001:3000"  # Frontend
     - "6380:6379"  # Redis
   ```

#### npm install fails
**Symptoms:** Frontend dependencies fail to install

**Solutions:**
1. Clear npm cache: `npm cache clean --force`
2. Delete node_modules: `rm -rf node_modules`
3. Delete package-lock.json
4. Run `npm install` again
5. Try using yarn instead: `yarn install`

#### pip install fails
**Symptoms:** Python dependencies fail to install

**Solutions:**
1. Upgrade pip: `pip install --upgrade pip`
2. Install build tools (Windows): Install Visual Studio Build Tools
3. Install build tools (Linux): `sudo apt-get install python3-dev`
4. Use Python 3.11: `python3.11 -m venv venv`

### Runtime Issues

#### Backend won't start
**Symptoms:** uvicorn crashes or won't start

**Solutions:**
1. Check Python version: `python --version` (need 3.11+)
2. Verify Redis is running: `docker ps | grep redis`
3. Check environment variables in backend/.env
4. Look for import errors in console
5. Ensure virtual environment is activated

#### Frontend won't start
**Symptoms:** npm run dev fails

**Solutions:**
1. Check Node version: `node --version` (need 18+)
2. Delete .vite cache: `rm -rf node_modules/.vite`
3. Verify backend is running on port 8000
4. Check frontend/.env for correct URLs
5. Clear browser cache

#### Redis connection failed
**Symptoms:** "Failed to connect to Redis" error

**Solutions:**
1. Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
2. Test connection: `redis-cli ping` (should return PONG)
3. Check REDIS_HOST in backend/.env:
   - Use "localhost" for local development
   - Use "redis" when running with docker-compose
4. Check firewall settings
5. Verify Redis port in config

### WebSocket Issues

#### Connection failed
**Symptoms:** "WebSocket connection failed" in browser console

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000`
2. Check CORS settings in backend/config.py
3. Ensure correct WebSocket URL in frontend/.env:
   ```
   VITE_WS_URL=ws://localhost:8000
   ```
4. Check browser console for detailed error
5. Disable browser extensions that might block WebSocket

#### Frequent disconnections
**Symptoms:** Constant reconnection messages

**Solutions:**
1. Check network stability
2. Increase heartbeat interval in backend/config.py
3. Check backend logs for errors
4. Verify Redis is stable: `redis-cli INFO`
5. Check for proxy/firewall interfering with WebSocket

#### Messages not syncing
**Symptoms:** Edits from other users not appearing

**Solutions:**
1. Verify all users are in the same room
2. Check connection status indicator (should be green)
3. Refresh the browser
4. Check backend logs: `docker-compose logs backend`
5. Verify Redis pub/sub is working:
   ```bash
   redis-cli
   SUBSCRIBE room:*
   ```

### Editor Issues

#### Monaco Editor not loading
**Symptoms:** Blank editor area

**Solutions:**
1. Check browser console for errors
2. Verify monaco-editor is installed: `npm list @monaco-editor/react`
3. Clear browser cache
4. Try different browser
5. Check network tab for failed CDN requests

#### Syntax highlighting not working
**Symptoms:** All code appears plain text

**Solutions:**
1. Verify language is set correctly
2. Check Monaco Editor configuration in App.jsx
3. Refresh the page
4. Try changing language and switching back

#### Cursor position incorrect
**Symptoms:** Your cursor appears in wrong location

**Solutions:**
1. This is usually a temporary sync issue
2. Refresh the page
3. Check for JavaScript errors in console
4. Verify operation transformation logic is working

### Performance Issues

#### Slow synchronization
**Symptoms:** Changes take several seconds to appear

**Solutions:**
1. Check network latency
2. Verify Redis is running locally (not remote)
3. Check backend CPU/memory usage
4. Reduce document size
5. Check for excessive number of users in room

#### High CPU usage
**Symptoms:** Computer becomes slow

**Solutions:**
1. Limit number of open tabs/rooms
2. Reduce number of concurrent users
3. Check for infinite loops in browser console
4. Restart Docker containers
5. Allocate more resources to Docker Desktop

#### Memory leaks
**Symptoms:** Application becomes slower over time

**Solutions:**
1. Refresh the browser tab
2. Close unused rooms
3. Restart backend: `docker-compose restart backend`
4. Check for WebSocket connection leaks
5. Monitor memory in browser DevTools

### Test Failures

#### pytest fails
**Symptoms:** Tests fail when running pytest

**Solutions:**
1. Ensure Redis is NOT running (tests don't need it)
2. Activate virtual environment
3. Install test dependencies: `pip install -r requirements.txt`
4. Check Python version: `python --version`
5. Run tests in verbose mode: `pytest tests/ -v -s`

#### Specific test fails
**Symptoms:** One or two tests fail consistently

**Solutions:**
1. Read the error message carefully
2. Check if the test is timing-dependent
3. Run the specific test: `pytest tests/test_file.py::TestClass::test_name -v`
4. Check for port conflicts
5. Ensure test database/state is clean

### Docker Issues

#### Container won't start
**Symptoms:** docker-compose up shows container exiting

**Solutions:**
1. Check logs: `docker-compose logs [service_name]`
2. Rebuild containers: `docker-compose up --build`
3. Remove volumes: `docker-compose down -v`
4. Check Dockerfile syntax
5. Verify base images are available

#### Volume permission errors
**Symptoms:** Permission denied errors in containers

**Solutions:**
1. On Linux, check file ownership
2. Run with correct user: `docker-compose run --user $(id -u):$(id -g)`
3. Check Docker Desktop file sharing settings
4. Reset Docker Desktop to factory defaults

#### Image build fails
**Symptoms:** docker-compose build fails

**Solutions:**
1. Check internet connection (for downloading base images)
2. Clear Docker cache: `docker system prune -a`
3. Check Dockerfile syntax
4. Verify requirements.txt and package.json are valid
5. Try building manually: `docker build -t test backend/`

### Production Issues

#### CORS errors in production
**Symptoms:** "CORS policy" errors in browser

**Solutions:**
1. Add production domain to CORS_ORIGINS in backend/.env
2. Ensure protocol matches (http vs https)
3. Include port if non-standard
4. Check Access-Control headers in network tab

#### HTTPS/WSS not working
**Symptoms:** WebSocket fails with secure connection

**Solutions:**
1. Ensure backend supports WSS
2. Configure reverse proxy (nginx/traefik) for WebSocket
3. Check SSL certificate validity
4. Update frontend to use wss:// instead of ws://
5. Verify proxy timeout settings for WebSocket

## Debug Mode

### Enable verbose logging

**Backend:**
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In websocket.js
const DEBUG = true;
if (DEBUG) console.log(...);
```

### Monitor WebSocket messages

**Browser DevTools:**
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by WS
4. Click on WebSocket connection
5. View Messages tab

### Monitor Redis

```bash
# Connect to Redis CLI
docker exec -it <redis-container> redis-cli

# Monitor all commands
MONITOR

# Check pub/sub channels
PUBSUB CHANNELS

# Check keys
KEYS *
```

### Check Backend Health

```bash
# Health check
curl http://localhost:8000

# Get room list
curl http://localhost:8000/api/rooms

# Check WebSocket (using wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws/test-room?username=Debug
```

## Getting Help

If you're still stuck:

1. Check the logs:
   - Backend: `docker-compose logs backend`
   - Frontend: Browser console (F12)
   - Redis: `docker-compose logs redis`

2. Search for error messages in:
   - GitHub Issues
   - Stack Overflow
   - FastAPI documentation
   - React documentation

3. Collect debugging information:
   - Error messages
   - Browser console output
   - Docker logs
   - System information
   - Steps to reproduce

4. Ask for help with:
   - Clear description of the problem
   - What you've tried
   - Error messages
   - System configuration
