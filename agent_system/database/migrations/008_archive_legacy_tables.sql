-- Phase 8: Archive Legacy Tables
-- This migration archives the old tables that have been replaced by the entity framework

-- Create archive schema for legacy tables
CREATE TABLE IF NOT EXISTS _archive_agents AS SELECT * FROM agents;
CREATE TABLE IF NOT EXISTS _archive_tasks AS SELECT * FROM tasks;
CREATE TABLE IF NOT EXISTS _archive_messages AS SELECT * FROM messages;
CREATE TABLE IF NOT EXISTS _archive_tools AS SELECT * FROM tools;
CREATE TABLE IF NOT EXISTS _archive_context_documents AS SELECT * FROM context_documents;

-- Add archive metadata
ALTER TABLE _archive_agents ADD COLUMN archived_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE _archive_tasks ADD COLUMN archived_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE _archive_messages ADD COLUMN archived_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE _archive_tools ADD COLUMN archived_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE _archive_context_documents ADD COLUMN archived_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Create views for compatibility during transition
CREATE VIEW agents_legacy AS 
SELECT 
    e.entity_id as id,
    e.name,
    a.instruction,
    a.context_documents,
    a.available_tools,
    a.permissions,
    a.constraints,
    e.state as status,
    a.model_config,
    e.created_at,
    e.updated_at
FROM entities e
JOIN agents a ON e.entity_id = a.id
WHERE e.entity_type = 'agent';

CREATE VIEW tasks_legacy AS
SELECT 
    e.entity_id as id,
    t.parent_task_id,
    t.tree_id,
    t.agent_id,
    t.instruction,
    t.context,
    e.state as status,
    t.result,
    e.created_at,
    t.completed_at,
    e.updated_at
FROM entities e
JOIN tasks t ON e.entity_id = t.id
WHERE e.entity_type = 'task';

CREATE VIEW tools_legacy AS
SELECT 
    e.entity_id as id,
    e.name,
    t.description,
    t.category,
    t.implementation,
    t.parameters,
    t.permissions,
    e.state as status,
    e.created_at,
    e.updated_at
FROM entities e
JOIN tools t ON e.entity_id = t.id
WHERE e.entity_type = 'tool';

-- Drop the original tables (after confirming data is safely archived)
-- IMPORTANT: Only run these drops after verifying all data is migrated
-- DROP TABLE agents;
-- DROP TABLE tasks;
-- DROP TABLE messages;
-- DROP TABLE tools;
-- DROP TABLE context_documents;

-- Create summary of archived data
CREATE VIEW archive_summary AS
SELECT 
    '_archive_agents' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    CURRENT_TIMESTAMP as archived_at
FROM _archive_agents
UNION ALL
SELECT 
    '_archive_tasks' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    CURRENT_TIMESTAMP as archived_at
FROM _archive_tasks
UNION ALL
SELECT 
    '_archive_messages' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    CURRENT_TIMESTAMP as archived_at
FROM _archive_messages
UNION ALL
SELECT 
    '_archive_tools' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    CURRENT_TIMESTAMP as archived_at
FROM _archive_tools
UNION ALL
SELECT 
    '_archive_context_documents' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    CURRENT_TIMESTAMP as archived_at
FROM _archive_context_documents;

-- Log the archival
INSERT INTO events (event_type, entity_type, entity_id, category, content, metadata, created_at)
VALUES (
    'SYSTEM_EVENT',
    'system',
    0,
    'migration',
    'Legacy tables archived',
    json_object(
        'phase', 8,
        'action', 'archive_legacy_tables',
        'tables_archived', json_array(
            'agents', 'tasks', 'messages', 'tools', 'context_documents'
        ),
        'archive_prefix', '_archive_',
        'compatibility_views_created', true
    ),
    CURRENT_TIMESTAMP
);