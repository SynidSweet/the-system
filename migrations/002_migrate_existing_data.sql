-- Migration 002: Migrate Existing Data to Entity Framework
-- This migration populates the new entity tables with existing data

-- 1. Populate entities table from existing agents
INSERT INTO entities (entity_type, entity_id, name, version, created_at, updated_at, created_by_task_id, status, metadata)
SELECT 
    'agent' as entity_type,
    id as entity_id,
    name,
    version,
    created_at,
    updated_at,
    created_by as created_by_task_id,
    status,
    json_object(
        'instruction_length', length(instruction),
        'has_context_docs', CASE WHEN context_documents IS NOT NULL AND context_documents != '[]' THEN 1 ELSE 0 END,
        'has_tools', CASE WHEN available_tools IS NOT NULL AND available_tools != '[]' THEN 1 ELSE 0 END
    ) as metadata
FROM agents
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.entity_type = 'agent' AND e.entity_id = agents.id
);

-- 2. Populate entities table from existing tools
INSERT INTO entities (entity_type, entity_id, name, version, created_at, updated_at, created_by_task_id, status, metadata)
SELECT 
    'tool' as entity_type,
    id as entity_id,
    name,
    version,
    created_at,
    created_at as updated_at, -- tools don't have updated_at
    created_by as created_by_task_id,
    status,
    json_object(
        'category', category,
        'has_dependencies', CASE WHEN dependencies IS NOT NULL AND dependencies != '[]' THEN 1 ELSE 0 END
    ) as metadata
FROM tools
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.entity_type = 'tool' AND e.entity_id = tools.id
);

-- 3. Populate entities table from existing documents
INSERT INTO entities (entity_type, entity_id, name, version, created_at, updated_at, created_by_task_id, status, metadata)
SELECT 
    'document' as entity_type,
    id as entity_id,
    name,
    version,
    created_at,
    updated_at,
    updated_by as created_by_task_id,
    'active' as status,
    json_object(
        'title', title,
        'category', category,
        'format', format,
        'access_level', access_level
    ) as metadata
FROM context_documents
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.entity_type = 'document' AND e.entity_id = context_documents.id
);

-- 4. Populate entities table from existing tasks
INSERT INTO entities (entity_type, entity_id, name, version, created_at, updated_at, created_by_task_id, status, metadata)
SELECT 
    'task' as entity_type,
    id as entity_id,
    'task_' || id as name,
    '1.0.0' as version,
    created_at,
    COALESCE(completed_at, started_at, created_at) as updated_at,
    parent_task_id as created_by_task_id,
    CASE 
        WHEN status IN ('complete', 'failed') THEN 'inactive'
        ELSE 'active'
    END as status,
    json_object(
        'tree_id', tree_id,
        'agent_id', agent_id,
        'original_status', status,
        'has_result', CASE WHEN result IS NOT NULL THEN 1 ELSE 0 END,
        'priority', priority
    ) as metadata
FROM tasks
WHERE NOT EXISTS (
    SELECT 1 FROM entities e 
    WHERE e.entity_type = 'task' AND e.entity_id = tasks.id
);

-- 5. Create entity relationships from agent tool usage
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, strength, context)
SELECT DISTINCT
    'agent' as source_type,
    a.id as source_id,
    'tool' as target_type,
    t.id as target_id,
    'uses' as relationship_type,
    1.0 as strength,
    json_object('configured', 1) as context
FROM agents a
CROSS JOIN tools t
WHERE EXISTS (
    SELECT 1 FROM json_each(a.available_tools) 
    WHERE json_each.value = t.name
)
AND NOT EXISTS (
    SELECT 1 FROM entity_relationships er
    WHERE er.source_type = 'agent' AND er.source_id = a.id
    AND er.target_type = 'tool' AND er.target_id = t.id
);

-- 6. Create entity relationships from agent document usage
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, strength, context)
SELECT DISTINCT
    'agent' as source_type,
    a.id as source_id,
    'document' as target_type,
    cd.id as target_id,
    'references' as relationship_type,
    1.0 as strength,
    json_object('configured', 1) as context
FROM agents a
CROSS JOIN context_documents cd
WHERE EXISTS (
    SELECT 1 FROM json_each(a.context_documents) 
    WHERE json_each.value = cd.name
)
AND NOT EXISTS (
    SELECT 1 FROM entity_relationships er
    WHERE er.source_type = 'agent' AND er.source_id = a.id
    AND er.target_type = 'document' AND er.target_id = cd.id
);

-- 7. Create entity relationships from task-agent assignments
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, strength, context)
SELECT DISTINCT
    'task' as source_type,
    t.id as source_id,
    'agent' as target_type,
    t.agent_id as target_id,
    'uses' as relationship_type,
    1.0 as strength,
    json_object('assignment', 'direct') as context
FROM tasks t
WHERE t.agent_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM entity_relationships er
    WHERE er.source_type = 'task' AND er.source_id = t.id
    AND er.target_type = 'agent' AND er.target_id = t.agent_id
);

-- 8. Create entity relationships from task hierarchy
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, strength, context)
SELECT DISTINCT
    'task' as source_type,
    t.parent_task_id as source_id,
    'task' as target_type,
    t.id as target_id,
    'creates' as relationship_type,
    1.0 as strength,
    json_object('hierarchy', 'parent-child') as context
FROM tasks t
WHERE t.parent_task_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM entity_relationships er
    WHERE er.source_type = 'task' AND er.source_id = t.parent_task_id
    AND er.target_type = 'task' AND er.target_id = t.id
);

-- 9. Convert system_events to events table
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, event_data, tree_id, timestamp)
SELECT 
    event_type,
    CASE 
        WHEN source_task_id IS NOT NULL THEN 'task'
        ELSE 'system'
    END as primary_entity_type,
    COALESCE(source_task_id, 0) as primary_entity_id,
    event_data,
    CASE 
        WHEN source_task_id IS NOT NULL THEN (SELECT tree_id FROM tasks WHERE id = source_task_id)
        ELSE NULL
    END as tree_id,
    timestamp
FROM system_events
WHERE NOT EXISTS (
    SELECT 1 FROM events e 
    WHERE e.timestamp = system_events.timestamp 
    AND e.event_type = system_events.event_type
);

-- 10. Convert messages to events for comprehensive tracking
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, related_entities, event_data, tree_id, timestamp)
SELECT 
    CASE message_type
        WHEN 'user_input' THEN 'AGENT_PROMPT_SENT'
        WHEN 'agent_response' THEN 'AGENT_RESPONSE_RECEIVED'
        WHEN 'tool_call' THEN 'TOOL_CALLED'
        WHEN 'tool_response' THEN 'TOOL_COMPLETED'
        WHEN 'system_event' THEN 'SYSTEM_EVENT'
        WHEN 'error' THEN 'SYSTEM_ERROR'
        ELSE 'SYSTEM_EVENT'
    END as event_type,
    'task' as primary_entity_type,
    task_id as primary_entity_id,
    json_object(
        'task', json_array(task_id),
        'agent', json_array((SELECT agent_id FROM tasks WHERE id = m.task_id))
    ) as related_entities,
    json_object(
        'message_type', message_type,
        'content_length', length(content),
        'token_count', token_count,
        'execution_time_ms', execution_time_ms,
        'metadata', metadata
    ) as event_data,
    (SELECT tree_id FROM tasks WHERE id = m.task_id) as tree_id,
    timestamp
FROM messages m
WHERE NOT EXISTS (
    SELECT 1 FROM events e 
    WHERE e.timestamp = m.timestamp 
    AND e.primary_entity_id = m.task_id
);

-- 11. Initialize rolling review counters for active agents
INSERT INTO rolling_review_counters (entity_type, entity_id, counter_type, threshold, review_frequency)
SELECT 
    'agent' as entity_type,
    id as entity_id,
    'usage' as counter_type,
    100 as threshold,
    'threshold' as review_frequency
FROM agents
WHERE status = 'active'
AND NOT EXISTS (
    SELECT 1 FROM rolling_review_counters rrc
    WHERE rrc.entity_type = 'agent' AND rrc.entity_id = agents.id
    AND rrc.counter_type = 'usage'
);

-- 12. Initialize rolling review counters for active tools
INSERT INTO rolling_review_counters (entity_type, entity_id, counter_type, threshold, review_frequency)
SELECT 
    'tool' as entity_type,
    id as entity_id,
    'usage' as counter_type,
    50 as threshold,
    'threshold' as review_frequency
FROM tools
WHERE status = 'active'
AND NOT EXISTS (
    SELECT 1 FROM rolling_review_counters rrc
    WHERE rrc.entity_type = 'tool' AND rrc.entity_id = tools.id
    AND rrc.counter_type = 'usage'
);

-- 13. Initialize entity effectiveness baselines
INSERT INTO entity_effectiveness (entity_type, entity_id, metric_name, metric_value, context)
SELECT 
    'agent' as entity_type,
    a.id as entity_id,
    'task_success_rate' as metric_name,
    CAST(COUNT(CASE WHEN t.status = 'complete' THEN 1 END) AS REAL) / NULLIF(COUNT(*), 0) as metric_value,
    json_object('total_tasks', COUNT(*), 'completed_tasks', COUNT(CASE WHEN t.status = 'complete' THEN 1 END)) as context
FROM agents a
LEFT JOIN tasks t ON t.agent_id = a.id
GROUP BY a.id
HAVING COUNT(*) > 0;