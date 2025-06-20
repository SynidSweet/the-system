-- Phase 7: Add self-improvement context and tools

-- Add self-improvement guide to context documents
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'self_improvement_guide',
    'Self-Improvement Guide',
    '# Self-Improvement Guide

[Full content from self_improvement_guide.md]',
    'guide',
    json_array('self_improvement', 'optimization', 'evolution', 'phase7'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Add request_improvement tool to tools table
INSERT INTO tools (id, name, description, category, implementation, parameters, permissions, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM tools),
    'request_improvement',
    'Request system improvements based on observations',
    'system',
    'agent_system.tools.request_improvement.RequestImprovementTool',
    json_object(
        'improvement_type', json_object(
            'type', 'string',
            'enum', json_array(
                'instruction_update',
                'context_optimization',
                'tool_reassignment',
                'process_automation',
                'performance_tuning',
                'error_prevention'
            ),
            'required', true
        ),
        'description', json_object('type', 'string', 'required', true),
        'rationale', json_object('type', 'string', 'required', true),
        'evidence', json_object('type', 'object', 'required', false)
    ),
    json_array('execute'),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Update optimizer agent to include self-improvement guide
UPDATE agents
SET context_documents = json_insert(
    context_documents,
    '$[#]', 'self_improvement_guide'
)
WHERE name = 'optimizer_agent';

-- Grant request_improvement tool to key agents
INSERT INTO agent_base_permissions (agent_type, entity_permissions, base_tools, max_concurrent_tools, created_at, updated_at)
VALUES 
    ('optimizer_agent', 
     json_object('optimization_opportunities', 'write', 'improvement_history', 'read'),
     json_insert(
        (SELECT base_tools FROM agent_base_permissions WHERE agent_type = 'optimizer_agent'),
        '$[#]', 'request_improvement'
     ),
     5,
     CURRENT_TIMESTAMP,
     CURRENT_TIMESTAMP)
ON CONFLICT(agent_type) DO UPDATE SET
    base_tools = json_insert(base_tools, '$[#]', 'request_improvement'),
    updated_at = CURRENT_TIMESTAMP;

-- Also grant to planning and recovery agents
UPDATE agent_base_permissions
SET base_tools = json_insert(base_tools, '$[#]', 'request_improvement'),
    updated_at = CURRENT_TIMESTAMP
WHERE agent_type IN ('planning_agent', 'recovery_agent');

-- Create improvement monitoring alert rules
CREATE TABLE IF NOT EXISTS improvement_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'high_rollback_rate', 'degraded_performance', 'stalled_improvement',
        'recurring_failure', 'opportunity_backlog'
    )),
    threshold REAL NOT NULL,
    current_value REAL,
    entity_type TEXT,
    entity_id INTEGER,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME,
    resolved_at DATETIME,
    metadata TEXT  -- JSON
);

-- Create index for active alerts
CREATE INDEX idx_improvement_alerts_active ON improvement_alerts(status, alert_type);

-- Initialize alert thresholds
INSERT INTO improvement_alerts (alert_type, threshold, metadata)
VALUES 
    ('high_rollback_rate', 0.3, json_object('description', 'More than 30% of improvements being rolled back')),
    ('degraded_performance', -0.2, json_object('description', 'System performance degraded by 20%')),
    ('opportunity_backlog', 50, json_object('description', 'More than 50 pending opportunities')),
    ('recurring_failure', 5, json_object('description', 'Same error occurring 5+ times per hour'));

-- Add self-improvement metrics to system status
CREATE VIEW system_self_improvement_status AS
SELECT 
    -- Overall metrics
    (SELECT COUNT(*) FROM improvement_history WHERE status = 'deployed') as total_improvements,
    (SELECT AVG(effectiveness) FROM improvement_history WHERE status = 'deployed') as avg_effectiveness,
    (SELECT COUNT(*) FROM improvement_history WHERE status = 'rolled_back') as total_rollbacks,
    (SELECT COUNT(*) FROM optimization_opportunities WHERE status = 'pending') as pending_opportunities,
    
    -- Recent activity (last 24 hours)
    (SELECT COUNT(*) FROM improvement_history WHERE created_at > datetime('now', '-24 hours')) as recent_attempts,
    (SELECT COUNT(*) FROM improvement_history WHERE status = 'deployed' AND created_at > datetime('now', '-24 hours')) as recent_successes,
    
    -- Top improved entities
    (SELECT json_group_array(
        json_object(
            'entity', entity_type || '_' || entity_id,
            'improvements', improvement_count,
            'avg_effectiveness', avg_effectiveness
        )
    ) FROM (
        SELECT entity_type, entity_id, 
               COUNT(*) as improvement_count,
               AVG(effectiveness) as avg_effectiveness
        FROM improvement_history
        WHERE status = 'deployed'
        GROUP BY entity_type, entity_id
        ORDER BY improvement_count DESC
        LIMIT 5
    )) as top_improved_entities,
    
    -- Active improvements
    (SELECT COUNT(*) FROM improvement_history WHERE status IN ('testing', 'validated')) as active_improvements,
    
    -- System health
    CASE 
        WHEN (SELECT COUNT(*) FROM improvement_alerts WHERE status = 'active') > 0 THEN 'needs_attention'
        WHEN (SELECT AVG(effectiveness) FROM improvement_history WHERE status = 'deployed' AND created_at > datetime('now', '-7 days')) > 0.1 THEN 'improving'
        WHEN (SELECT COUNT(*) FROM improvement_history WHERE created_at > datetime('now', '-24 hours')) = 0 THEN 'idle'
        ELSE 'stable'
    END as health_status;

-- Grant all Phase 7 agents permission to view improvement status
UPDATE entities
SET metadata = json_set(
    metadata,
    '$.can_view_improvements', true,
    '$.participates_in_evolution', true
)
WHERE name IN (
    'planning_agent', 'investigator_agent', 'optimizer_agent',
    'recovery_agent', 'feedback_agent'
);

-- Log Phase 7 activation
INSERT INTO events (event_type, entity_type, entity_id, category, content, metadata, created_at)
VALUES (
    'SYSTEM_EVENT',
    'system',
    0,
    'phase_activation',
    'Phase 7: Self-Improvement Activation completed',
    json_object(
        'phase', 7,
        'components', json_array(
            'self_improvement_engine',
            'improvement_dashboard',
            'request_improvement_tool',
            'improvement_processes',
            'monitoring_alerts'
        ),
        'capabilities', json_array(
            'automatic_optimization',
            'pattern_based_improvements',
            'effectiveness_tracking',
            'safety_mechanisms',
            'agent_participation'
        )
    ),
    CURRENT_TIMESTAMP
);