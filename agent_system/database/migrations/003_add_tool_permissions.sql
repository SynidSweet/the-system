-- Migration: Add Tool Permission System Tables
-- This migration adds the database schema for the optional tooling system

-- Base permissions for each agent type
CREATE TABLE IF NOT EXISTS agent_base_permissions (
    agent_type TEXT PRIMARY KEY,
    entity_permissions JSON NOT NULL,     -- {"agent": ["read"], "task": ["read", "write"]}
    base_tools JSON NOT NULL,            -- ["entity_manager", "message_user"]
    max_concurrent_tools INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic tool assignments to specific tasks
CREATE TABLE IF NOT EXISTS task_tool_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    tool_name TEXT NOT NULL,
    tool_permissions JSON,               -- Tool-specific permissions
    assigned_by_agent_id INTEGER,        -- Which agent assigned this tool
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,                -- Optional expiration
    assignment_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (assigned_by_agent_id) REFERENCES tasks(id),
    UNIQUE(task_id, tool_name)          -- Prevent duplicate assignments
);

-- Tool usage tracking for optimization
CREATE TABLE IF NOT EXISTS tool_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    agent_type TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    operation TEXT,                      -- Specific tool operation used
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    execution_time_ms INTEGER,
    parameters_hash TEXT,                -- Hash of parameters for pattern analysis
    result_summary TEXT,
    error_message TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Tool definitions and capabilities
CREATE TABLE IF NOT EXISTS available_tools (
    tool_name TEXT PRIMARY KEY,
    tool_type TEXT NOT NULL,             -- "mcp_server", "internal", "external"
    description TEXT,
    mcp_server_url TEXT,                 -- For MCP tools
    available_operations JSON,           -- List of operations this tool supports
    security_level TEXT DEFAULT 'standard', -- "minimal", "standard", "elevated"
    configuration JSON,                  -- Tool-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_tool_assignments_task ON task_tool_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_tool_assignments_active ON task_tool_assignments(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_tool_usage_events_task ON tool_usage_events(task_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_events_tool ON tool_usage_events(tool_name, used_at);
CREATE INDEX IF NOT EXISTS idx_tool_usage_events_agent ON tool_usage_events(agent_type, used_at);

-- Create view for active tool assignments
CREATE VIEW IF NOT EXISTS active_tool_assignments AS
SELECT 
    tta.*,
    t.instruction as task_instruction,
    t.status as task_status
FROM task_tool_assignments tta
JOIN tasks t ON tta.task_id = t.id
WHERE tta.is_active = TRUE 
AND (tta.expires_at IS NULL OR tta.expires_at > datetime('now'));

-- Create view for tool usage statistics
CREATE VIEW IF NOT EXISTS tool_usage_stats AS
SELECT 
    tool_name,
    agent_type,
    COUNT(*) as usage_count,
    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
    AVG(execution_time_ms) as avg_execution_time,
    MIN(used_at) as first_used,
    MAX(used_at) as last_used
FROM tool_usage_events
GROUP BY tool_name, agent_type;

-- Insert base agent permissions
INSERT INTO agent_base_permissions (agent_type, entity_permissions, base_tools) VALUES
('agent_selector', '{"agent": ["read"], "task": ["read", "write"]}', '["entity_manager"]'),
('planning_agent', '{"task": ["read", "write"], "process": ["read"]}', '["entity_manager"]'),
('context_addition', '{"document": ["read", "write"], "task": ["read"]}', '["entity_manager", "file_system_listing"]'),
('tool_addition', '{"tool": ["read", "write"], "task": ["read", "write"]}', '["entity_manager", "file_system_listing"]'),
('task_evaluator', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('summary_agent', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('documentation_agent', '{"document": ["read", "write"], "task": ["read"]}', '["entity_manager", "file_system_listing"]'),
('review_agent', '{"all": ["read"], "agent": ["write"], "process": ["write"]}', '["entity_manager", "sql_lite", "file_system_listing"]'),
('feedback_agent', '{"task": ["read"], "event": ["read"]}', '["entity_manager"]'),
('request_validation', '{"task": ["read"], "tool": ["read"]}', '["entity_manager"]'),
('investigator_agent', '{"all": ["read"]}', '["entity_manager", "sql_lite"]'),
('optimizer_agent', '{"all": ["read", "write"]}', '["entity_manager", "sql_lite"]'),
('recovery_agent', '{"all": ["read", "write"]}', '["entity_manager", "sql_lite", "terminal"]');

-- Insert available tools registry
INSERT INTO available_tools (tool_name, tool_type, description, available_operations, security_level) VALUES
('entity_manager', 'mcp_server', 'Core entity CRUD operations', '["get_agent", "update_agent", "create_agent", "list_agents", "get_task", "update_task", "create_task", "get_task_dependencies", "get_process", "list_processes", "get_document", "create_document", "update_document", "search_documents", "get_tool", "list_tools", "get_events", "log_event"]', 'minimal'),
('message_user', 'mcp_server', 'Send messages to user', '["send_message", "send_structured_message"]', 'minimal'),
('file_system_listing', 'mcp_server', 'List and read files', '["list_files", "read_file", "file_exists"]', 'standard'),
('file_edit', 'mcp_server', 'Edit and write files', '["write_file", "create_file", "append_to_file"]', 'elevated'),
('sql_lite', 'mcp_server', 'Database queries', '["execute_query", "list_available_queries"]', 'standard'),
('terminal', 'mcp_server', 'System commands', '["execute_command", "list_allowed_commands"]', 'elevated'),
('github', 'mcp_server', 'Git operations', '["git_status", "git_log", "git_diff", "git_commit", "git_push", "git_branch"]', 'elevated');

-- Add trigger to update timestamps
CREATE TRIGGER IF NOT EXISTS update_agent_base_permissions_timestamp 
AFTER UPDATE ON agent_base_permissions
BEGIN
    UPDATE agent_base_permissions SET updated_at = CURRENT_TIMESTAMP WHERE agent_type = NEW.agent_type;
END;

CREATE TRIGGER IF NOT EXISTS update_available_tools_timestamp 
AFTER UPDATE ON available_tools
BEGIN
    UPDATE available_tools SET updated_at = CURRENT_TIMESTAMP WHERE tool_name = NEW.tool_name;
END;