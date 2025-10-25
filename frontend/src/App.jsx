import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Toaster, toast } from 'react-hot-toast';
import { Users, Wifi, WifiOff } from 'lucide-react';
import WebSocketService from './services/websocket';
import ApiService from './services/api';
import './index.css';

function App() {
  const [view, setView] = useState('landing'); // 'landing' or 'editor'
  const [roomId, setRoomId] = useState('');
  const [username, setUsername] = useState('');
  const [language, setLanguage] = useState('python');
  const [joinRoomId, setJoinRoomId] = useState('');
  const [joinUsername, setJoinUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Editor state
  const [editorContent, setEditorContent] = useState('');
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [currentUserColor, setCurrentUserColor] = useState('#4ECDC4');
  const [connectionState, setConnectionState] = useState('disconnected');
  const [cursors, setCursors] = useState(new Map());

  const wsRef = useRef(null);
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorationsRef = useRef([]);
  const localChangesRef = useRef(false);

  // Initialize WebSocket service
  useEffect(() => {
    wsRef.current = new WebSocketService();
    wsRef.current.onStateChange = setConnectionState;

    // Register message handlers
    wsRef.current.on('init', handleInit);
    wsRef.current.on('operation', handleOperation);
    wsRef.current.on('cursor', handleCursor);
    wsRef.current.on('user_joined', handleUserJoined);
    wsRef.current.on('user_left', handleUserLeft);

    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);

  // Update cursor decorations
  useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      updateCursorDecorations();
    }
  }, [cursors, users]);

  const handleCreateRoom = async () => {
    if (!username.trim()) {
      setError('Please enter a username');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const room = await ApiService.createRoom(language);
      setRoomId(room.room_id);
      
      // Connect to WebSocket
      wsRef.current.connect(room.room_id, username);
      setView('editor');
    } catch (err) {
      setError(err.message);
      toast.error('Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinRoom = async () => {
    if (!joinRoomId.trim() || !joinUsername.trim()) {
      setError('Please enter room ID and username');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Verify room exists
      await ApiService.getRoom(joinRoomId);
      
      setRoomId(joinRoomId);
      setUsername(joinUsername);
      
      // Connect to WebSocket
      wsRef.current.connect(joinRoomId, joinUsername);
      setView('editor');
    } catch (err) {
      setError(err.message);
      toast.error('Failed to join room');
    } finally {
      setLoading(false);
    }
  };

  const handleInit = (message) => {
    console.log('Initialized:', message);
    setCurrentUserId(message.userId);
    setCurrentUserColor(message.color);
    setEditorContent(message.document.content);
    setUsers(message.users || []);
    toast.success('Connected to room');
  };

  const handleOperation = (message) => {
    if (message.userId === currentUserId) {
      return; // Ignore own operations
    }

    const operation = message.operation;
    const editor = editorRef.current;
    
    if (!editor) return;

    localChangesRef.current = true;

    const model = editor.getModel();
    if (!model) return;

    try {
      if (operation.type === 'insert') {
        const position = model.getPositionAt(operation.position);
        const range = new monacoRef.current.Range(
          position.lineNumber,
          position.column,
          position.lineNumber,
          position.column
        );
        model.pushEditOperations(
          [],
          [{ range, text: operation.content }],
          () => null
        );
      } else if (operation.type === 'delete') {
        const startPos = model.getPositionAt(operation.position);
        const endPos = model.getPositionAt(operation.position + operation.content.length);
        const range = new monacoRef.current.Range(
          startPos.lineNumber,
          startPos.column,
          endPos.lineNumber,
          endPos.column
        );
        model.pushEditOperations(
          [],
          [{ range, text: '' }],
          () => null
        );
      }
    } finally {
      localChangesRef.current = false;
    }
  };

  const handleCursor = (message) => {
    setCursors(prev => {
      const next = new Map(prev);
      next.set(message.userId, {
        position: message.position,
        selectionStart: message.selectionStart,
        selectionEnd: message.selectionEnd,
      });
      return next;
    });
  };

  const handleUserJoined = (message) => {
    setUsers(prev => {
      // Check if user already exists
      if (prev.find(u => u.userId === message.user.userId)) {
        return prev;
      }
      return [...prev, message.user];
    });
    toast.success(`${message.user.username} joined the session`);
  };

  const handleUserLeft = (message) => {
    setUsers(prev => prev.filter(u => u.userId !== message.userId));
    setCursors(prev => {
      const next = new Map(prev);
      next.delete(message.userId);
      return next;
    });
    toast(`${message.username} left the session`, {
      icon: '👋',
    });
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Store content before changes to capture deleted text
    let contentBeforeChange = '';
    
    editor.onDidChangeModelContent((e) => {
      if (localChangesRef.current) return;

      const model = editor.getModel();
      if (!model) return;

      // Process changes
      for (const change of e.changes) {
        const position = model.getOffsetAt({
          lineNumber: change.range.startLineNumber,
          column: change.range.startColumn,
        });

        let operation;
        if (change.text) {
          // Insert operation
          operation = {
            type: 'insert',
            position: position,
            content: change.text,
          };
        } else {
          // Delete operation
          // Use rangeLength as the content length indicator
          operation = {
            type: 'delete',
            position: position,
            content: '\0'.repeat(change.rangeLength),
          };
        }

        // Send operation to server
        wsRef.current.send({
          type: 'operation',
          operation,
        });
      }
    });

    // Listen for cursor position changes
    editor.onDidChangeCursorPosition((e) => {
      const model = editor.getModel();
      if (!model) return;

      const position = model.getOffsetAt(e.position);
      const selection = editor.getSelection();
      
      let selectionStart = null;
      let selectionEnd = null;
      
      if (selection && !selection.isEmpty()) {
        selectionStart = model.getOffsetAt(selection.getStartPosition());
        selectionEnd = model.getOffsetAt(selection.getEndPosition());
      }

      wsRef.current.send({
        type: 'cursor',
        position,
        selectionStart,
        selectionEnd,
      });
    });
  };

  const updateCursorDecorations = () => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const model = editor?.getModel();
    
    if (!editor || !monaco || !model) return;

    const newDecorations = [];

    // Create decorations for each user's cursor
    users.forEach(user => {
      if (user.userId === currentUserId) return;

      const cursorData = cursors.get(user.userId);
      if (!cursorData) return;

      const position = model.getPositionAt(cursorData.position);

      // Cursor decoration
      newDecorations.push({
        range: new monaco.Range(
          position.lineNumber,
          position.column,
          position.lineNumber,
          position.column
        ),
        options: {
          className: 'remote-cursor',
          beforeContentClassName: 'remote-cursor-marker',
          stickiness: 1,
          hoverMessage: { value: user.username },
          zIndex: 1000,
        },
      });

      // Selection decoration
      if (cursorData.selectionStart !== null && cursorData.selectionEnd !== null) {
        const startPos = model.getPositionAt(cursorData.selectionStart);
        const endPos = model.getPositionAt(cursorData.selectionEnd);
        
        newDecorations.push({
          range: new monaco.Range(
            startPos.lineNumber,
            startPos.column,
            endPos.lineNumber,
            endPos.column
          ),
          options: {
            className: 'remote-selection',
            inlineClassName: 'remote-selection-inline',
            stickiness: 1,
          },
        });
      }
    });

    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current,
      newDecorations
    );
  };

  const copyRoomId = () => {
    navigator.clipboard.writeText(roomId);
    toast.success('Room ID copied to clipboard');
  };

  if (view === 'landing') {
    return (
      <div className="landing-page">
        <Toaster position="top-right" />
        <div className="landing-content">
          <h1>Collaborative Code Editor</h1>
          <p>Real-time collaborative editing with conflict-free synchronization</p>

          <div className="action-section">
            <h2>Create New Room</h2>
            <div className="select-group">
              <label>Programming Language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="go">Go</option>
              </select>
            </div>
            <div className="input-group">
              <input
                type="text"
                placeholder="Your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateRoom()}
              />
              <button className="btn" onClick={handleCreateRoom} disabled={loading}>
                {loading ? 'Creating...' : 'Create Room'}
              </button>
            </div>
          </div>

          <div className="divider">OR</div>

          <div className="action-section">
            <h2>Join Existing Room</h2>
            <div className="input-group">
              <input
                type="text"
                placeholder="Room ID"
                value={joinRoomId}
                onChange={(e) => setJoinRoomId(e.target.value)}
              />
            </div>
            <div className="input-group">
              <input
                type="text"
                placeholder="Your username"
                value={joinUsername}
                onChange={(e) => setJoinUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleJoinRoom()}
              />
              <button className="btn" onClick={handleJoinRoom} disabled={loading}>
                {loading ? 'Joining...' : 'Join Room'}
              </button>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Toaster position="top-right" />
      
      <header className="header">
        <h1>Collaborative Code Editor</h1>
        <div className="room-info">
          <div className="room-id" onClick={copyRoomId} style={{ cursor: 'pointer' }}>
            <span>Room:</span>
            <code>{roomId}</code>
          </div>
          <div className="connection-status">
            <div className={`status-indicator ${connectionState}`}></div>
            <span>{connectionState === 'connected' ? 'Connected' : connectionState === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      <div className="main-content">
        <div className="editor-container">
          <Editor
            height="100%"
            language={language}
            theme="vs-dark"
            value={editorContent}
            onMount={handleEditorDidMount}
            options={{
              minimap: { enabled: true },
              fontSize: 14,
              wordWrap: 'on',
              automaticLayout: true,
              scrollBeyondLastLine: false,
              renderLineHighlight: 'all',
              cursorBlinking: 'smooth',
              cursorSmoothCaretAnimation: true,
            }}
          />
        </div>

        <aside className="sidebar">
          <div className="sidebar-header">
            <Users size={16} style={{ marginRight: '8px', display: 'inline' }} />
            Active Users ({users.length})
          </div>
          <div className="users-list">
            {users.map(user => (
              <div
                key={user.userId}
                className={`user-item ${user.userId === currentUserId ? 'current-user' : ''}`}
              >
                <div className="user-color" style={{ backgroundColor: user.color }}></div>
                <div className="user-name">{user.username}</div>
                {user.userId === currentUserId && <div className="user-badge">You</div>}
              </div>
            ))}
          </div>
        </aside>
      </div>

      <style>{`
        .remote-cursor-marker::before {
          content: '';
          position: absolute;
          width: 2px;
          height: 20px;
          background-color: ${currentUserColor};
          animation: blink 1s infinite;
        }

        .remote-selection {
          background-color: rgba(79, 195, 247, 0.2);
        }

        @keyframes blink {
          0%, 49% { opacity: 1; }
          50%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}

export default App;
