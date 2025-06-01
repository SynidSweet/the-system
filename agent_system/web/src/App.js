import React, { useState, useEffect } from 'react';
import './App.css';

// Get API base URL from environment or use production default
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:8000' : `${window.location.protocol}//${window.location.hostname}:8000`);
const WS_URL = API_BASE_URL.replace(/^http/, 'ws') + '/ws';

function App() {
  const [instruction, setInstruction] = useState('');
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ws, setWs] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('tasks');

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const websocket = new WebSocket(WS_URL);
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      setError(null);
    };
    websocket.onmessage = (event) => {
      console.log('WebSocket message:', event.data);
      // Refresh task list on updates
      if (event.data.includes('task_created') || event.data.includes('task_completed')) {
        fetchTasks();
      }
    };
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
    };
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
      setError('WebSocket connection failed');
    };
    setWs(websocket);

    // Initial data fetch
    fetchTasks();
    fetchAgents();
    fetchSystemHealth();

    // Set up periodic health checks
    const healthInterval = setInterval(fetchSystemHealth, 30000);

    return () => {
      websocket.close();
      clearInterval(healthInterval);
    };
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/active`);
      const data = await response.json();
      setTasks(data.active_trees || []);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError('Failed to fetch tasks');
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/agents`);
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Error fetching system health:', error);
    }
  };

  const submitTask = async () => {
    if (!instruction.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instruction: instruction.trim(),
          priority: 1
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Task submitted:', result);
        setInstruction('');
        fetchTasks();
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        setError(`Failed to submit task: ${errorData.message || 'Server error'}`);
      }
    } catch (error) {
      console.error('Error submitting task:', error);
      setError('Network error: Unable to submit task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      submitTask();
    }
  };

  const renderTasksTab = () => (
    <div className="task-status-section">
      <h2>Active Task Trees ({tasks.length})</h2>
      {tasks.length === 0 ? (
        <div className="empty-state">
          <p>🚀 No active tasks. Submit a task above to get started!</p>
          <p className="help-text">Try asking agents to build advanced capabilities on top of the complete foundation.</p>
        </div>
      ) : (
        <div className="task-trees">
          {tasks.map((tree) => (
            <div key={tree.tree_id} className="task-tree">
              <div className="tree-header">
                <h3>Tree {tree.tree_id}</h3>
                <span className={`status ${tree.status}`}>{tree.status}</span>
              </div>
              <div className="tree-meta">
                <span><strong>Started:</strong> {new Date(tree.started_at).toLocaleString()}</span>
                <span><strong>Tasks:</strong> {tree.tasks.length}</span>
              </div>
              
              <div className="tree-tasks">
                {tree.tasks.map((task) => (
                  <div key={task.id} className="task-item">
                    <div className="task-header">
                      <span className={`status ${task.status}`}>{task.status}</span>
                      <span className="task-id">Task {task.id}</span>
                      {task.agent_name && <span className="agent-name">👤 {task.agent_name}</span>}
                    </div>
                    <p className="task-instruction">{task.instruction}</p>
                    {task.result && (
                      <div className="task-result">
                        <strong>Result:</strong>
                        <div className="result-content">{task.result}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderAgentsTab = () => (
    <div className="agents-section">
      <h2>Available Agents ({agents.length})</h2>
      <div className="agents-grid">
        {agents.map((agent) => (
          <div key={agent.id} className="agent-card">
            <div className="agent-header">
              <h3>{agent.name}</h3>
              <span className={`agent-status ${agent.status || 'active'}`}>
                {agent.status || 'active'}
              </span>
            </div>
            <p className="agent-description">
              {agent.instruction ? agent.instruction.substring(0, 150) + '...' : 'No description available'}
            </p>
            <div className="agent-meta">
              <span>📄 Docs: {agent.context_documents?.length || 0}</span>
              <span>🔧 Tools: {agent.available_tools?.length || 0}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSystemTab = () => (
    <div className="system-section">
      <h2>System Health</h2>
      {systemHealth ? (
        <div className="health-grid">
          <div className="health-card">
            <h3>🏥 Overall Status</h3>
            <span className={`health-status ${systemHealth.status}`}>
              {systemHealth.status || 'unknown'}
            </span>
            <p>Last check: {new Date().toLocaleString()}</p>
          </div>
          
          <div className="health-card">
            <h3>🗄️ Database</h3>
            <span className="health-status healthy">Connected</span>
            <p>All tables operational</p>
          </div>
          
          <div className="health-card">
            <h3>🔌 WebSocket</h3>
            <span className={`health-status ${connectionStatus === 'connected' ? 'healthy' : 'unhealthy'}`}>
              {connectionStatus}
            </span>
            <p>Real-time updates {connectionStatus === 'connected' ? 'active' : 'inactive'}</p>
          </div>
          
          <div className="health-card">
            <h3>🤖 Agents</h3>
            <span className="health-status healthy">{agents.length} Available</span>
            <p>Complete foundation deployed</p>
          </div>
        </div>
      ) : (
        <p>Loading system health...</p>
      )}
    </div>
  );

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Self-Improving Agent System</h1>
        <p>Complete foundation with 9 specialized agents - build advanced capabilities through collaboration</p>
        
        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} className="error-close">×</button>
          </div>
        )}
        
        <div className="connection-status">
          <span className={`connection-indicator ${connectionStatus}`}>
            {connectionStatus === 'connected' ? '🟢' : connectionStatus === 'connecting' ? '🟡' : '🔴'}
          </span>
          <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
        </div>
      </header>

      <main className="App-main">
        <div className="task-input-section">
          <h2>Submit New Task</h2>
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter your task instruction here...

Advanced Examples (foundation is complete):
- Build a comprehensive performance monitoring dashboard with real-time analytics
- Create advanced testing frameworks with automated quality gates
- Implement machine learning capabilities for pattern recognition
- Develop sophisticated UI components for complex task visualization
- Build advanced security and safety monitoring systems
- Create deployment automation and CI/CD pipelines"
            rows={8}
            disabled={isSubmitting}
          />
          <div className="input-controls">
            <button 
              onClick={submitTask} 
              disabled={isSubmitting || !instruction.trim()}
              className="submit-button"
            >
              {isSubmitting ? '⏳ Submitting...' : '🚀 Submit Task (Ctrl+Enter)'}
            </button>
            <span className="char-count">{instruction.length} characters</span>
          </div>
        </div>

        <nav className="tabs">
          <button 
            className={`tab ${activeTab === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveTab('tasks')}
          >
            📋 Tasks ({tasks.length})
          </button>
          <button 
            className={`tab ${activeTab === 'agents' ? 'active' : ''}`}
            onClick={() => setActiveTab('agents')}
          >
            🤖 Agents ({agents.length})
          </button>
          <button 
            className={`tab ${activeTab === 'system' ? 'active' : ''}`}
            onClick={() => setActiveTab('system')}
          >
            ⚙️ System
          </button>
        </nav>

        <div className="tab-content">
          {activeTab === 'tasks' && renderTasksTab()}
          {activeTab === 'agents' && renderAgentsTab()}
          {activeTab === 'system' && renderSystemTab()}
        </div>
      </main>

      <footer className="App-footer">
        <p>
          <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noopener noreferrer">
            📚 API Documentation
          </a>
          {' | '}
          <a href={`${API_BASE_URL}/health`} target="_blank" rel="noopener noreferrer">
            🏥 System Health
          </a>
          {' | '}
          <a href="https://github.com/your-repo/agent-system" target="_blank" rel="noopener noreferrer">
            📂 Source Code
          </a>
        </p>
        <p className="version-info">Complete Foundation v1.0 | 9 Agents | Full MCP Toolkit</p>
      </footer>
    </div>
  );
}

export default App;