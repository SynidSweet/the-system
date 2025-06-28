import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import ErrorBoundary from './components/ErrorBoundary';
import ThreadList from './components/ThreadList';
import MessageStream from './components/MessageStream';
import TaskTreeVisualization from './components/TaskTreeVisualization';
import ControlPanel from './components/ControlPanel';
import AgentBrowser from './components/AgentBrowser';
import ToolBrowser from './components/ToolBrowser';
import DocumentBrowser from './components/DocumentBrowser';
import InitializationPage from './components/InitializationPage';
import { useWebSocket } from './hooks/useWebSocket';
import {
  SystemState,
  CurrentView,
  ConnectionStatus,
  SystemConfig,
  TaskThread,
  Message,
  PausedTask,
  WebSocketMessage,
  InitializationSettings,
  TasksResponse,
  TaskSubmissionResponse,
  ThreadMessagesResponse
} from './types';

// Get API base URL from environment or use production default
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname === 'localhost' ? 'http://localhost:8000' : `${window.location.protocol}//${window.location.hostname}/api`);
const WS_URL = process.env.REACT_APP_WS_URL || 
  (window.location.hostname === 'localhost' ? 'ws://localhost:8000/ws' : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}/api/ws`);

const App: React.FC = () => {
  // System state
  const [systemState, setSystemState] = useState<SystemState>('loading');
  const [currentView, setCurrentView] = useState<CurrentView>('tasks');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  
  // Task and thread state
  const [threads, setThreads] = useState<TaskThread[]>([]);
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [showCompleted, setShowCompleted] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [pausedTasks, setPausedTasks] = useState<PausedTask[]>([]);
  
  // UI state
  const [showTaskTree, setShowTaskTree] = useState<boolean>(false);
  const [instruction, setInstruction] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  
  // System configuration
  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    max_parallel_tasks: 3,
    step_mode: false,
    step_mode_threads: [],
    manual_step_mode: false,
    max_concurrent_agents: 3
  });

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'system_state_change':
        if (message.state) {
          setSystemState(message.state);
          if (message.state === 'ready') {
            fetchThreads();
            fetchSystemConfig();
          }
        }
        break;
        
      case 'agent_started':
      case 'agent_thinking':
      case 'agent_tool_call':
      case 'agent_tool_result':
      case 'agent_completed':
      case 'agent_error':
      case 'step_mode_pause':
        setMessages(prev => [...prev, message as Message]);
        
        if (message.type === 'step_mode_pause') {
          setPausedTasks(prev => [...prev, message as PausedTask]);
        }
        break;
        
      case 'task_created':
      case 'task_completed':
      case 'thread_update':
        fetchThreads();
        break;
        
      case 'config_updated':
        if (message.config) {
          setSystemConfig(message.config);
        }
        break;
        
      case 'step_continued':
        if (message.task_id) {
          setPausedTasks(prev => prev.filter(t => t.task_id !== message.task_id));
        }
        break;
    }
  }, []);

  // WebSocket hook
  const { sendMessage } = useWebSocket({
    url: WS_URL,
    onMessage: handleWebSocketMessage,
    onConnectionStatusChange: setConnectionStatus
  });

  // Effects
  useEffect(() => {
    checkSystemState();
    fetchThreads();
    fetchSystemConfig();
  }, []);

  // API functions
  const checkSystemState = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/system/state`);
      const data = await response.json();
      setSystemState(data.state);
    } catch (error) {
      console.error('Error checking system state:', error);
      setSystemState('uninitialized');
    }
  };

  const fetchThreads = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/all`);
      const data: TasksResponse = await response.json();
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

  const loadThreadMessages = async (threadId: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/tree/${threadId}/messages`);
      const data: ThreadMessagesResponse = await response.json();
      
      setMessages(prev => {
        const filtered = prev.filter(m => m.tree_id !== threadId);
        return [...filtered, ...data.messages];
      });
    } catch (error) {
      console.error('Error loading thread messages:', error);
    }
  };

  const fetchSystemConfig = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/system/config`);
      const config = await response.json();
      setSystemConfig(config);
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const updateSystemConfig = async (newConfig: SystemConfig): Promise<void> => {
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

  // Event handlers
  const handleInitialize = async (settings: InitializationSettings): Promise<void> => {
    try {
      await updateSystemConfig({
        ...systemConfig,
        manual_step_mode: settings.manualStepMode,
        max_concurrent_agents: settings.maxConcurrentAgents,
        step_mode: settings.manualStepMode,
        step_mode_threads: ['*']
      });

      const response = await fetch(`${API_BASE_URL}/system/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        setSystemState('initializing');
      }
    } catch (error) {
      console.error('Error starting initialization:', error);
    }
  };

  const submitTask = async (e: React.FormEvent): Promise<void> => {
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
        const result: TaskSubmissionResponse = await response.json();
        setInstruction('');
        setSelectedThread(result.tree_id);
        fetchThreads();
      }
    } catch (error) {
      console.error('Error submitting task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const continueTask = (taskId: number): void => {
    sendMessage({
      type: 'continue_step',
      task_id: taskId
    });
  };

  const handleSelectThread = (threadId: string | null, showComp?: boolean): void => {
    setSelectedThread(threadId);
    if (showComp !== undefined) {
      setShowCompleted(showComp);
    }
    if (threadId) {
      loadThreadMessages(threadId);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && e.ctrlKey) {
      submitTask(e as any);
    }
  };

  // Render different states
  if (systemState === 'uninitialized') {
    return (
      <ErrorBoundary>
        <InitializationPage onInitialize={handleInitialize} />
      </ErrorBoundary>
    );
  }

  if (systemState === 'loading') {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Checking system state...</p>
      </div>
    );
  }

  if (systemState === 'initializing') {
    return (
      <div className="app">
        <div className="app-header">
          <h1>🤖 Agent System - Initializing</h1>
        </div>
        <div className="app-body">
          <div className="initialization-progress">
            <h2>System Initialization in Progress</h2>
            <p>The system is executing initialization tasks. You can monitor progress below.</p>
            <p>With manual step mode enabled, approve each agent execution in the Tasks view.</p>
            <button 
              className="view-tasks-button"
              onClick={() => window.location.reload()}
            >
              View Task Progress
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
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
            <ErrorBoundary fallback={<div>Error loading tasks view</div>}>
              <div className="sidebar">
                <ThreadList
                  threads={threads}
                  selectedThread={selectedThread}
                  onSelectThread={handleSelectThread}
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
                  
                  {selectedThread && (
                    <div className="view-toggle">
                      <button
                        className={`toggle-button ${!showTaskTree ? 'active' : ''}`}
                        onClick={() => setShowTaskTree(false)}
                      >
                        📜 Messages
                      </button>
                      <button
                        className={`toggle-button ${showTaskTree ? 'active' : ''}`}
                        onClick={() => setShowTaskTree(true)}
                      >
                        📊 Tree View
                      </button>
                    </div>
                  )}
                </div>
                
                {selectedThread ? (
                  showTaskTree ? (
                    <ErrorBoundary fallback={<div>Error loading task tree</div>}>
                      <TaskTreeVisualization
                        threadId={selectedThread}
                        apiBaseUrl={API_BASE_URL}
                      />
                    </ErrorBoundary>
                  ) : (
                    <ErrorBoundary fallback={<div>Error loading messages</div>}>
                      <MessageStream
                        messages={messages}
                        threadId={selectedThread}
                      />
                    </ErrorBoundary>
                  )
                ) : (
                  <div className="no-thread-selected">
                    Select a thread or submit a new task to get started
                  </div>
                )}
              </div>
              
              <div className="control-sidebar">
                <ErrorBoundary fallback={<div>Error loading control panel</div>}>
                  <ControlPanel
                    systemConfig={systemConfig}
                    onUpdateConfig={updateSystemConfig}
                    selectedThread={selectedThread}
                    pausedTasks={pausedTasks.filter(t => t.tree_id === selectedThread)}
                    onContinueTask={continueTask}
                  />
                </ErrorBoundary>
              </div>
            </ErrorBoundary>
          )}
          
          {currentView === 'agents' && (
            <ErrorBoundary fallback={<div>Error loading agents view</div>}>
              <AgentBrowser apiBaseUrl={API_BASE_URL} />
            </ErrorBoundary>
          )}
          
          {currentView === 'tools' && (
            <ErrorBoundary fallback={<div>Error loading tools view</div>}>
              <ToolBrowser apiBaseUrl={API_BASE_URL} />
            </ErrorBoundary>
          )}
          
          {currentView === 'documents' && (
            <ErrorBoundary fallback={<div>Error loading documents view</div>}>
              <DocumentBrowser apiBaseUrl={API_BASE_URL} />
            </ErrorBoundary>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default App;