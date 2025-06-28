-- Create agents table with proper schema
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    name TEXT NOT NULL,
    instruction TEXT,
    context_documents TEXT DEFAULT '[]',
    available_tools TEXT DEFAULT '[]',
    permissions TEXT DEFAULT '[]',
    constraints TEXT DEFAULT '[]'
);

-- Create tasks table with proper schema  
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    parent_task_id INTEGER,
    tree_id INTEGER,
    agent_id INTEGER,
    instruction TEXT,
    status TEXT DEFAULT 'created',
    result TEXT DEFAULT '{}',
    metadata TEXT DEFAULT '{}'
);

-- Create other entity tables that might be needed
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    function_name TEXT,
    parameters TEXT DEFAULT '{}',
    returns TEXT DEFAULT '{}',
    category TEXT
);

CREATE TABLE IF NOT EXISTS context_documents (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    title TEXT,
    content TEXT,
    category TEXT DEFAULT 'general',
    format TEXT DEFAULT 'text',
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS process_definitions (
    id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    process_type TEXT,
    trigger_events TEXT DEFAULT '[]',
    parameters TEXT DEFAULT '{}'
);