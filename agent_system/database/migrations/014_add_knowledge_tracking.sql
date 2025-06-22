-- Add knowledge tracking to support MVP knowledge system
-- This migration adds fields and tables for tracking knowledge usage and gaps

-- Add knowledge tracking columns to tasks table
ALTER TABLE tasks ADD COLUMN context_package_id VARCHAR(255);
ALTER TABLE tasks ADD COLUMN knowledge_gaps TEXT;
ALTER TABLE tasks ADD COLUMN context_completeness_score FLOAT DEFAULT 0.0;

-- Knowledge usage tracking table
CREATE TABLE IF NOT EXISTS knowledge_usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_entity_id VARCHAR(255) NOT NULL,
    task_id INTEGER NOT NULL,
    agent_type VARCHAR(255),
    usage_type VARCHAR(255), -- 'context_assembly', 'validation', 'gap_detection', 'learning'
    effectiveness_score FLOAT,
    metadata TEXT, -- JSON for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Knowledge gap tracking table
CREATE TABLE IF NOT EXISTS knowledge_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    gap_type VARCHAR(255), -- 'missing_context', 'incomplete_context', 'execution_failure_pattern', 'missing_domain_knowledge'
    gap_description TEXT,
    priority VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    resolved BOOLEAN DEFAULT FALSE,
    resolution_entity_id VARCHAR(255), -- ID of knowledge entity that resolved this gap
    metadata TEXT, -- JSON for additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Knowledge evolution tracking
CREATE TABLE IF NOT EXISTS knowledge_evolution_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_task_id INTEGER,
    knowledge_entity_id VARCHAR(255),
    evolution_type VARCHAR(255), -- 'created', 'updated', 'relationship_added', 'effectiveness_improved'
    previous_state TEXT, -- JSON snapshot of previous state
    new_state TEXT, -- JSON snapshot of new state
    trigger_event VARCHAR(255), -- What triggered this evolution
    metadata TEXT, -- JSON for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_task_id) REFERENCES tasks(id)
);

-- Context assembly history
CREATE TABLE IF NOT EXISTS context_assembly_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    agent_type VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    knowledge_sources TEXT, -- JSON array of knowledge entity IDs used
    completeness_score FLOAT,
    missing_requirements TEXT, -- JSON array of missing requirements
    context_size INTEGER,
    assembly_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Add index for performance
CREATE INDEX idx_knowledge_usage_entity ON knowledge_usage_events(knowledge_entity_id);
CREATE INDEX idx_knowledge_usage_task ON knowledge_usage_events(task_id);
CREATE INDEX idx_knowledge_gaps_task ON knowledge_gaps(task_id);
CREATE INDEX idx_knowledge_gaps_priority ON knowledge_gaps(priority, resolved);
CREATE INDEX idx_context_assembly_task ON context_assembly_history(task_id);

-- Update entity metadata to support knowledge entities
UPDATE entities
SET metadata = json_set(
    COALESCE(metadata, '{}'),
    '$.supports_knowledge_system', true,
    '$.knowledge_integration_version', '1.0.0'
)
WHERE entity_type = 'system' AND name = 'system_config';

-- Add knowledge system configuration
INSERT OR REPLACE INTO documents (name, title, category, content, format, version, status, metadata)
VALUES (
    'knowledge_system_config',
    'Knowledge System Configuration',
    'system_configuration',
    '{
        "system_type": "mvp_file_based",
        "storage_backend": "json_files",
        "knowledge_directory": "knowledge",
        "context_assembly": {
            "max_context_size": 10000,
            "relevance_threshold": 0.3,
            "max_entities_per_context": 20
        },
        "knowledge_evolution": {
            "effectiveness_threshold": 0.7,
            "usage_count_threshold": 10,
            "auto_relationship_discovery": true
        },
        "gap_detection": {
            "completeness_threshold": 0.8,
            "auto_gap_resolution": false,
            "priority_levels": ["low", "medium", "high", "critical"]
        }
    }',
    'json',
    '1.0.0',
    'active',
    json_object(
        'created_by', 'migration_014',
        'purpose', 'MVP knowledge system configuration',
        'integration_ready', true
    )
);

-- Add knowledge-aware process
INSERT OR IGNORE INTO processes (name, description, category, steps, parameters, permissions, status, metadata)
VALUES (
    'knowledge_aware_task_execution',
    'Task execution with knowledge context assembly and gap detection',
    'task_execution',
    json_array(
        'Assemble knowledge context for task',
        'Validate context completeness',
        'Execute task with enriched context',
        'Analyze execution for knowledge gaps',
        'Update knowledge effectiveness scores',
        'Create new knowledge from successful patterns'
    ),
    json_object(
        'min_completeness_score', 0.8,
        'track_knowledge_usage', true,
        'detect_gaps', true,
        'evolve_knowledge', true
    ),
    json_object(
        'required', json_array('task_execute', 'knowledge_read', 'knowledge_write'),
        'optional', json_array('knowledge_evolve')
    ),
    'active',
    json_object(
        'created_by', 'migration_014',
        'knowledge_integrated', true
    )
);

-- Log the knowledge system activation
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, event_data, metadata)
VALUES (
    'SYSTEM_UPDATE',
    'system',
    0,
    json_object(
        'action', 'knowledge_system_activation',
        'description', 'Activated MVP knowledge system with file-based storage'
    ),
    json_object(
        'migration', '014_add_knowledge_tracking',
        'features', json_array(
            'context_assembly',
            'gap_detection',
            'usage_tracking',
            'knowledge_evolution'
        )
    )
);