-- Cleanup migration for process-first architecture
-- This ensures consistency after the process-first transformation

-- Update any remaining references to 8 agents in metadata
UPDATE entities
SET metadata = json_set(
    COALESCE(metadata, '{}'),
    '$.agent_count', 9,
    '$.architecture', 'process-first'
)
WHERE entity_type = 'document' 
  AND (metadata LIKE '%8 agents%' OR metadata LIKE '%Complete Foundation%');

-- Ensure process_discovery has proper model preferences
UPDATE entities
SET metadata = json_set(
    COALESCE(metadata, '{}'),
    '$.model_preference', 'gemini-2.5-flash',
    '$.model_config', json_object(
        'provider', 'google',
        'temperature', 0.1,
        'max_tokens', 4000
    )
)
WHERE entity_type = 'agent' 
  AND name = 'process_discovery';

-- Add process-first metadata to system configuration
INSERT OR REPLACE INTO entities (entity_type, entity_id, name, metadata, status)
VALUES (
    'document',
    (SELECT entity_id FROM entities WHERE entity_type = 'document' AND name = 'system_config' 
     UNION SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'document'),
    'system_config',
    json_object(
        'architecture', 'process-first',
        'version', '2.0',
        'agent_count', 9,
        'primary_process', 'process_discovery_process',
        'core_principle', 'systematic framework establishment before execution',
        'features', json_array(
            'process discovery',
            'framework establishment', 
            'isolated task success',
            'systematic boundaries',
            'process optimization'
        )
    ),
    'active'
);

-- Update any task_breakdown references in config to planning_agent for consistency
UPDATE entities
SET metadata = json_set(
    COALESCE(metadata, '{}'),
    '$.model_preference', 
    CASE 
        WHEN json_extract(metadata, '$.model_preference') = 'task_breakdown' 
        THEN 'planning_agent'
        ELSE json_extract(metadata, '$.model_preference')
    END
)
WHERE entity_type = 'agent' AND metadata IS NOT NULL;

-- Add process-first validation document
INSERT OR IGNORE INTO documents (name, title, category, content, status, metadata)
VALUES (
    'process_first_validation',
    'Process-First Validation Checklist',
    'system_guides',
    '# Process-First Validation Checklist

Before any task execution, validate:

1. [ ] Process framework exists for the domain
2. [ ] Framework is complete and validated
3. [ ] Subtasks can succeed in isolation
4. [ ] All agents understand process-first principles
5. [ ] No ad-hoc execution paths remain

This ensures systematic operation.',
    'active',
    '{"version": "1.0", "process_first": true}'
);