/**
 * WebSocket service for real-time communication with the backend.
 * Handles connection lifecycle, reconnection, and message handling.
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const RECONNECT_DELAY = 2000;
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 30000;

export class WebSocketService {
  constructor() {
    this.ws = null;
    this.roomId = null;
    this.username = null;
    this.reconnectAttempts = 0;
    this.reconnectTimeout = null;
    this.heartbeatInterval = null;
    this.messageHandlers = new Map();
    this.connectionState = 'disconnected';
    this.onStateChange = null;
  }

  /**
   * Connect to a room via WebSocket
   * @param {string} roomId - Room identifier
   * @param {string} username - User's display name
   */
  connect(roomId, username) {
    this.roomId = roomId;
    this.username = username;
    this.reconnectAttempts = 0;
    this._connect();
  }

  _connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this._updateState('connecting');

    const url = `${WS_URL}/ws/${this.roomId}?username=${encodeURIComponent(this.username)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this._updateState('connected');
      this.reconnectAttempts = 0;
      this._startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this._handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this._updateState('disconnected');
      this._stopHeartbeat();
      this._attemptReconnect();
    };
  }

  /**
   * Send a message to the server
   * @param {object} message - Message to send
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  /**
   * Register a message handler for a specific message type
   * @param {string} type - Message type
   * @param {Function} handler - Handler function
   */
  on(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
  }

  /**
   * Unregister a message handler
   * @param {string} type - Message type
   * @param {Function} handler - Handler function to remove
   */
  off(type, handler) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Disconnect from the server
   */
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this._stopHeartbeat();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this._updateState('disconnected');
  }

  /**
   * Get current connection state
   * @returns {string} Connection state
   */
  getState() {
    return this.connectionState;
  }

  _handleMessage(message) {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }

  _updateState(state) {
    this.connectionState = state;
    if (this.onStateChange) {
      this.onStateChange(state);
    }
  }

  _attemptReconnect() {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Reconnecting... (attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);

    this.reconnectTimeout = setTimeout(() => {
      this._connect();
    }, RECONNECT_DELAY);
  }

  _startHeartbeat() {
    this._stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, HEARTBEAT_INTERVAL);
  }

  _stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}

export default WebSocketService;
