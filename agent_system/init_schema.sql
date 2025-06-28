CREATE TABLE IF NOT EXISTS entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    state TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    instruction TEXT,
    status TEXT DEFAULT 'created',
    assigned_agent TEXT,
    parent_task_id INTEGER,
    tree_id INTEGER,
    dependencies TEXT,
    result TEXT,
    priority INTEGER DEFAULT 1,
    max_execution_time INTEGER
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    instruction TEXT,
    context_documents TEXT,
    available_tools TEXT,
    model_config TEXT,
    permissions TEXT
);

-- Insert some default agents to make the system work
INSERT OR IGNORE INTO entities (entity_id, entity_type, name, description) VALUES 
(1, 'agent', 'agent_selector', 'Routes tasks to appropriate specialized agents'),
(2, 'agent', 'task_breakdown', 'Decomposes complex tasks into manageable subtasks'),
(3, 'agent', 'context_addition', 'Adds relevant context and knowledge to tasks'),
(4, 'agent', 'tool_addition', 'Develops and adds new tools and capabilities'),
(5, 'agent', 'task_evaluator', 'Evaluates task completion quality and outcomes'),
(6, 'agent', 'documentation_agent', 'Creates and maintains system documentation'),
(7, 'agent', 'summary_agent', 'Synthesizes and summarizes task results'),
(8, 'agent', 'review_agent', 'Reviews and improves system performance');

INSERT OR IGNORE INTO agents (id, instruction, context_documents, available_tools) VALUES 
(1, 'Route incoming tasks to the most appropriate specialized agent based on task requirements.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(2, 'Break down complex tasks into smaller, manageable subtasks that can be executed by specialized agents.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(3, 'Add relevant context, knowledge, and documentation to enhance task execution.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(4, 'Develop new tools and capabilities to expand the system''s functionality.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(5, 'Evaluate the quality and completeness of task executions and provide feedback.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(6, 'Create, update, and maintain comprehensive system documentation.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(7, 'Synthesize and summarize task results into clear, actionable insights.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]'),
(8, 'Review system performance and implement improvements for better efficiency.', '[]', '["break_down_task","start_subtask","request_context","request_tools","end_task","flag_for_review"]');