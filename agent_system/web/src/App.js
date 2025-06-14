import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ThreadList from './components/ThreadList';
import MessageStream from './components/MessageStream';
import ControlPanel from './components/ControlPanel';
import AgentBrowser from './components/AgentBrowser';
import ToolBrowser from './components/ToolBrowser';
import DocumentBrowser from './components/DocumentBrowser';

// Get API base URL from environment or use production default
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:8000' : `${window.location.protocol}//${window.location.hostname}/api`);
const WS_URL = process.env.REACT_APP_WS_URL || 
  (window.location.hostname === 'localhost' ? 'ws://localhost:8000/ws' : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}/api/ws`);

function App() {
  const [currentView, setCurrentView] = useState('tasks'); // 'tasks', 'agents', 'tools', 'documents'
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [pausedTasks, setPausedTasks] = useState([]);
  const [systemConfig, setSystemConfig] = useState({
    max_parallel_tasks: 3,
    step_mode: false,
    step_mode_threads: []
  });
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      connectWebSocket();
    }
    
    // Initial data fetch
    fetchThreads();
    fetchSystemConfig();

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const connectWebSocket = () => {
    // Prevent multiple connections
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || 
        wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }
    
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setConnectionStatus('disconnected');
      wsRef.current = null;
      setTimeout(connectWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };
  };

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'agent_started':
      case 'agent_thinking':
      case 'agent_tool_call':
      case 'agent_tool_result':
      case 'agent_completed':
      case 'agent_error':
      case 'step_mode_pause':
        setMessages(prev => [...prev, message]);
        
        if (message.type === 'step_mode_pause') {
          setPausedTasks(prev => [...prev, message]);
        }
        break;
        
      case 'task_created':
      case 'task_completed':
      case 'thread_update':
        fetchThreads();
        break;
        
      case 'config_updated':
        setSystemConfig(message.config);
        break;
        
      case 'step_continued':
        setPausedTasks(prev => prev.filter(t => t.task_id !== message.task_id));
        break;
    }
  };

  const fetchThreads = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/all`);
      const data = await response.json();
      setThreads(data.all_trees || []);
      
      // Auto-select first active thread if none selected
      if (!selectedThread && data.all_trees?.length > 0) {
        const activeThread = data.all_trees.find(t => t.has_running_tasks);
        if (activeThread) {
          setSelectedThread(activeThread.tree_id);
        }
      }
    } catch (error) {
      console.error('Error fetching threads:', error);
    }
  };
  
  const loadThreadMessages = async (threadId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/tree/${threadId}/messages`);
      const data = await response.json();
      
      // Add historical messages to the state
      setMessages(prev => {
        // Remove existing messages for this thread to avoid duplicates
        const filtered = prev.filter(m => m.tree_id !== threadId);
        return [...filtered, ...data.messages];
      });
    } catch (error) {
      console.error('Error loading thread messages:', error);
    }
  };

  const fetchSystemConfig = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/system/config`);
      const config = await response.json();
      setSystemConfig(config);
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const updateSystemConfig = async (newConfig) => {
    try {
      const response = await fetch(`${API_BASE_URL}/system/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      
      if (response.ok) {
        const result = await response.json();
        setSystemConfig(result.config);
      }
    } catch (error) {
      console.error('Error updating config:', error);
    }
  };

  const submitTask = async (e) => {
    e.preventDefault();
    if (!instruction.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction })
      });

      if (response.ok) {
        const result = await response.json();
        setInstruction('');
        // Auto-select the new thread
        setSelectedThread(result.tree_id);
        fetchThreads();
      }
    } catch (error) {
      console.error('Error submitting task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const continueTask = async (taskId) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'continue_step',
        task_id: taskId
      }));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      submitTask(e);
    }
  };

  return (
    <div className="app">
      <div className="app-header">
        <h1>🤖 Self-Improving Agent System</h1>
        <nav className="app-nav">
          <button 
            className={`nav-button ${currentView === 'tasks' ? 'active' : ''}`}
            onClick={() => setCurrentView('tasks')}
          >
            Tasks
          </button>
          <button 
            className={`nav-button ${currentView === 'agents' ? 'active' : ''}`}
            onClick={() => setCurrentView('agents')}
          >
            Agents
          </button>
          <button 
            className={`nav-button ${currentView === 'tools' ? 'active' : ''}`}
            onClick={() => setCurrentView('tools')}
          >
            Tools
          </button>
          <button 
            className={`nav-button ${currentView === 'documents' ? 'active' : ''}`}
            onClick={() => setCurrentView('documents')}
          >
            Documents
          </button>
        </nav>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus}`}></span>
          {connectionStatus}
        </div>
      </div>
      
      <div className="app-body">
        {currentView === 'tasks' && (
          <>
            <div className="sidebar">
              <ThreadList
                threads={threads}
                selectedThread={selectedThread}
                onSelectThread={(threadId, showComp) => {
                  setSelectedThread(threadId);
                  setShowCompleted(showComp);
                  if (threadId) {
                    loadThreadMessages(threadId);
                  }
                }}
                showCompleted={showCompleted}
              />
            </div>
            
            <div className="main-content">
              <div className="task-input-section">
                <form onSubmit={submitTask} className="task-form">
                  <input
                    type="text"
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter a task instruction..."
                    className="task-input"
                    disabled={isSubmitting}
                  />
                  <button 
                    type="submit" 
                    disabled={!instruction.trim() || isSubmitting}
                    className="submit-button"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Task'}
                  </button>
                </form>
              </div>
              
              {selectedThread ? (
                <MessageStream
                  messages={messages}
                  threadId={selectedThread}
                />
              ) : (
                <div className="no-thread-selected">
                  Select a thread or submit a new task to get started
                </div>
              )}
            </div>
            
            <div className="control-sidebar">
              <ControlPanel
                systemConfig={systemConfig}
                onUpdateConfig={updateSystemConfig}
                selectedThread={selectedThread}
                pausedTasks={pausedTasks.filter(t => t.tree_id === selectedThread)}
                onContinueTask={continueTask}
              />
            </div>
          </>
        )}
        
        {currentView === 'agents' && (
          <AgentBrowser apiBaseUrl={API_BASE_URL} />
        )}
        
        {currentView === 'tools' && (
          <ToolBrowser apiBaseUrl={API_BASE_URL} />
        )}
        
        {currentView === 'documents' && (
          <DocumentBrowser apiBaseUrl={API_BASE_URL} />
        )}
      </div>
    </div>
  );
}

export default App;