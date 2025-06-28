// System Types
export type SystemState = 'loading' | 'uninitialized' | 'initializing' | 'ready';
export type CurrentView = 'tasks' | 'agents' | 'tools' | 'documents';
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// Configuration Types
export interface SystemConfig {
  max_parallel_tasks: number;
  step_mode: boolean;
  step_mode_threads: string[];
  manual_step_mode: boolean;
  max_concurrent_agents: number;
}

export interface InitializationSettings {
  manualStepMode: boolean;
  maxConcurrentAgents: number;
}

// Task and Thread Types
export interface TaskThread {
  tree_id: string;
  root_task: {
    task_id: number;
    instruction: string;
    status: string;
    created_at: string;
  };
  task_count: number;
  has_running_tasks: boolean;
  last_activity: string;
}

export interface Message {
  type: MessageType;
  task_id: number;
  tree_id: string;
  agent_name?: string;
  timestamp: string;
  content: MessageContent;
}

export type MessageType = 
  | 'agent_started'
  | 'agent_thinking'
  | 'agent_tool_call'
  | 'agent_tool_result'
  | 'agent_completed'
  | 'agent_error'
  | 'step_mode_pause'
  | 'system_message'
  | 'user_message'
  | 'task_created'
  | 'task_completed'
  | 'thread_update'
  | 'config_updated'
  | 'step_continued'
  | 'system_state_change';

export interface MessageContent {
  message?: string;
  thought?: string;
  instruction?: string;
  error?: string;
  reason?: string;
  status?: string;
  tool_name?: string;
  tool_input?: any;
  tool_output?: any;
  success?: boolean;
}

export interface PausedTask {
  task_id: number;
  tree_id: string;
  type: 'step_mode_pause';
  content: {
    reason: string;
  };
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: MessageType;
  task_id?: number;
  tree_id?: string;
  state?: SystemState;
  config?: SystemConfig;
  messages?: Message[];
  [key: string]: any;
}

// API Response Types
export interface TasksResponse {
  all_trees: TaskThread[];
}

export interface TaskSubmissionResponse {
  tree_id: string;
  task_id: number;
}

export interface ThreadMessagesResponse {
  messages: Message[];
}

// Component Props Types
export interface ThreadListProps {
  threads: TaskThread[];
  selectedThread: string | null;
  onSelectThread: (threadId: string | null, showCompleted?: boolean) => void;
  showCompleted: boolean;
}

export interface MessageStreamProps {
  messages: Message[];
  threadId: string;
}

export interface ControlPanelProps {
  systemConfig: SystemConfig;
  onUpdateConfig: (config: SystemConfig) => void;
  selectedThread: string | null;
  pausedTasks: PausedTask[];
  onContinueTask: (taskId: number) => void;
}

export interface AgentBrowserProps {
  apiBaseUrl: string;
}

export interface ToolBrowserProps {
  apiBaseUrl: string;
}

export interface DocumentBrowserProps {
  apiBaseUrl: string;
}

export interface InitializationPageProps {
  onInitialize: (settings: InitializationSettings) => void;
}

// Error Boundary Types
export interface ErrorInfo {
  componentStack: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}