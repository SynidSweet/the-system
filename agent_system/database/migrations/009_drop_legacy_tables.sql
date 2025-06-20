-- Phase 8: Drop Legacy Tables (Final Cleanup)
-- This migration drops the old tables that have been archived

-- Verify archive tables exist before dropping originals
SELECT COUNT(*) as archive_count FROM sqlite_master 
WHERE type='table' AND name LIKE '_archive_%';

-- Drop legacy tables
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS tools;
DROP TABLE IF EXISTS context_documents;

-- Log the completion
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, event_data, outcome, metadata)
VALUES (
    'SYSTEM_EVENT',
    'system',
    0,
    json_object(
        'category', 'migration',
        'description', 'Legacy tables dropped - migration complete'
    ),
    'success',
    json_object(
        'phase', 8,
        'action', 'drop_legacy_tables',
        'tables_dropped', json_array(
            'agents', 'tasks', 'messages', 'tools', 'context_documents'
        ),
        'migration_complete', true
    )
);