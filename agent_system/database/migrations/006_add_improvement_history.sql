-- Phase 7: Self-Improvement Activation
-- Add improvement history tracking table

CREATE TABLE IF NOT EXISTS improvement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    improvement_id TEXT UNIQUE NOT NULL,
    improvement_type TEXT NOT NULL CHECK (improvement_type IN (
        'instruction_update', 'context_optimization', 'tool_reassignment',
        'process_automation', 'performance_tuning', 'error_prevention'
    )),
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'proposed', 'validated', 'testing', 'deployed', 'rolled_back', 'rejected'
    )),
    effectiveness REAL,
    metrics_before TEXT,  -- JSON
    metrics_after TEXT,   -- JSON
    deployed_at DATETIME,
    evaluated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (entity_type, entity_id) REFERENCES entities(entity_type, entity_id)
);

-- Index for querying improvements by entity
CREATE INDEX idx_improvement_history_entity ON improvement_history(entity_type, entity_id);

-- Index for querying by status
CREATE INDEX idx_improvement_history_status ON improvement_history(status);

-- Index for querying by effectiveness
CREATE INDEX idx_improvement_history_effectiveness ON improvement_history(effectiveness);

-- Add self-improvement configuration to entities
ALTER TABLE entities ADD COLUMN improvement_config TEXT DEFAULT json_object(
    'auto_improve_enabled', true,
    'min_confidence_threshold', 0.8,
    'test_duration_hours', 24,
    'max_rollback_rate', 0.1
);

-- Create view for improvement analytics
CREATE VIEW improvement_analytics AS
SELECT 
    ih.entity_type,
    ih.entity_id,
    e.name as entity_name,
    COUNT(*) as total_improvements,
    SUM(CASE WHEN ih.status = 'deployed' THEN 1 ELSE 0 END) as successful_improvements,
    SUM(CASE WHEN ih.status = 'rolled_back' THEN 1 ELSE 0 END) as rolled_back_improvements,
    AVG(ih.effectiveness) as avg_effectiveness,
    MAX(ih.effectiveness) as best_improvement,
    MIN(ih.effectiveness) as worst_improvement,
    MAX(ih.evaluated_at) as last_improvement_date
FROM improvement_history ih
JOIN entities e ON ih.entity_type = e.entity_type AND ih.entity_id = e.entity_id
GROUP BY ih.entity_type, ih.entity_id, e.name;

-- Add improvement metrics to optimization opportunities
ALTER TABLE optimization_opportunities ADD COLUMN implementation_history TEXT;  -- JSON array of improvement attempts

-- Create trigger to auto-create optimization opportunities from repeated errors
CREATE TRIGGER auto_create_error_opportunities
AFTER INSERT ON events
WHEN NEW.event_type = 'ERROR'
BEGIN
    INSERT OR IGNORE INTO optimization_opportunities (
        entity_type, entity_id, opportunity_type, description,
        potential_impact, confidence_score, status, metadata
    )
    SELECT 
        NEW.entity_type,
        NEW.entity_id,
        'error_reduction',
        'Frequent error pattern: ' || NEW.content,
        'high',
        0.9,
        'pending',
        json_object(
            'error_type', NEW.metadata->>'$.error_type',
            'frequency', (
                SELECT COUNT(*) 
                FROM events 
                WHERE entity_type = NEW.entity_type 
                  AND entity_id = NEW.entity_id
                  AND event_type = 'ERROR'
                  AND metadata->>'$.error_type' = NEW.metadata->>'$.error_type'
                  AND created_at > datetime('now', '-24 hours')
            )
        )
    WHERE (
        SELECT COUNT(*) 
        FROM events 
        WHERE entity_type = NEW.entity_type 
          AND entity_id = NEW.entity_id
          AND event_type = 'ERROR'
          AND metadata->>'$.error_type' = NEW.metadata->>'$.error_type'
          AND created_at > datetime('now', '-24 hours')
    ) > 5;  -- More than 5 errors of same type in 24 hours
END;

-- Create trigger to auto-create optimization opportunities from performance degradation
CREATE TRIGGER auto_create_performance_opportunities
AFTER INSERT ON events
WHEN NEW.event_type IN ('TASK_COMPLETED', 'TOOL_EXECUTED')
  AND CAST(NEW.metadata->>'$.duration' AS REAL) > 0
BEGIN
    INSERT OR IGNORE INTO optimization_opportunities (
        entity_type, entity_id, opportunity_type, description,
        potential_impact, confidence_score, status, metadata
    )
    SELECT 
        NEW.entity_type,
        NEW.entity_id,
        'performance',
        'Performance degradation detected in ' || NEW.content,
        'medium',
        0.85,
        'pending',
        json_object(
            'current_duration', NEW.metadata->>'$.duration',
            'baseline_duration', (
                SELECT AVG(CAST(metadata->>'$.duration' AS REAL))
                FROM events 
                WHERE entity_type = NEW.entity_type 
                  AND entity_id = NEW.entity_id
                  AND event_type = NEW.event_type
                  AND created_at < datetime('now', '-7 days')
                  AND created_at > datetime('now', '-14 days')
            ),
            'degradation_factor', (
                CAST(NEW.metadata->>'$.duration' AS REAL) / 
                NULLIF((
                    SELECT AVG(CAST(metadata->>'$.duration' AS REAL))
                    FROM events 
                    WHERE entity_type = NEW.entity_type 
                      AND entity_id = NEW.entity_id
                      AND event_type = NEW.event_type
                      AND created_at < datetime('now', '-7 days')
                      AND created_at > datetime('now', '-14 days')
                ), 0)
            )
        )
    WHERE (
        -- Duration is 50% higher than baseline
        CAST(NEW.metadata->>'$.duration' AS REAL) > 1.5 * (
            SELECT AVG(CAST(metadata->>'$.duration' AS REAL))
            FROM events 
            WHERE entity_type = NEW.entity_type 
              AND entity_id = NEW.entity_id
              AND event_type = NEW.event_type
              AND created_at < datetime('now', '-7 days')
              AND created_at > datetime('now', '-14 days')
        )
    );
END;

-- Add improvement-related event types to event type enum
-- (These should be added to the EventType enum in the code)
-- IMPROVEMENT_PROPOSED
-- IMPROVEMENT_VALIDATED
-- IMPROVEMENT_DEPLOYED
-- IMPROVEMENT_EVALUATED
-- IMPROVEMENT_ROLLED_BACK

-- Create self-improvement monitoring view
CREATE VIEW self_improvement_status AS
SELECT 
    e.entity_type,
    e.entity_id,
    e.name,
    e.state,
    e.improvement_config->>'$.auto_improve_enabled' as auto_improve_enabled,
    COALESCE(ia.total_improvements, 0) as total_improvements,
    COALESCE(ia.successful_improvements, 0) as successful_improvements,
    COALESCE(ia.avg_effectiveness, 0) as avg_effectiveness,
    ia.last_improvement_date,
    (
        SELECT COUNT(*) 
        FROM optimization_opportunities oo
        WHERE oo.entity_type = e.entity_type 
          AND oo.entity_id = e.entity_id
          AND oo.status = 'pending'
    ) as pending_opportunities,
    (
        SELECT COUNT(*)
        FROM rolling_review_counters rrc
        WHERE rrc.entity_type = e.entity_type
          AND rrc.entity_id = e.entity_id
          AND (
            (rrc.review_trigger_type = 'threshold' AND rrc.task_count >= rrc.review_interval)
            OR
            (rrc.review_trigger_type = 'periodic' 
             AND datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now'))
          )
    ) as pending_reviews
FROM entities e
LEFT JOIN improvement_analytics ia ON e.entity_type = ia.entity_type AND e.entity_id = ia.entity_id
WHERE e.state = 'active';

-- Add self-improvement metrics summary
CREATE VIEW self_improvement_metrics AS
SELECT 
    COUNT(DISTINCT entity_type || '_' || entity_id) as entities_improved,
    COUNT(*) as total_improvements,
    SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed_improvements,
    SUM(CASE WHEN status = 'rolled_back' THEN 1 ELSE 0 END) as rolled_back_improvements,
    AVG(effectiveness) as overall_effectiveness,
    SUM(CASE WHEN effectiveness > 0 THEN 1 ELSE 0 END) as positive_improvements,
    SUM(CASE WHEN effectiveness < 0 THEN 1 ELSE 0 END) as negative_improvements,
    json_group_array(
        json_object(
            'type', improvement_type,
            'count', type_count,
            'avg_effectiveness', avg_type_effectiveness
        )
    ) as improvements_by_type
FROM (
    SELECT 
        improvement_type,
        COUNT(*) as type_count,
        AVG(effectiveness) as avg_type_effectiveness
    FROM improvement_history
    WHERE status = 'deployed'
    GROUP BY improvement_type
) type_stats
CROSS JOIN improvement_history;

-- Initialize self-improvement for Phase 7 agents
UPDATE entities
SET improvement_config = json_object(
    'auto_improve_enabled', true,
    'min_confidence_threshold', 0.9,  -- Higher threshold for new agents
    'test_duration_hours', 48,         -- Longer test period
    'max_rollback_rate', 0.05          -- More conservative
)
WHERE name IN (
    'planning_agent', 'investigator_agent', 'optimizer_agent', 
    'recovery_agent', 'feedback_agent'
);

-- Create initial optimization opportunities for system improvement
INSERT INTO optimization_opportunities (entity_type, entity_id, opportunity_type, description, potential_impact, confidence_score, status, metadata)
VALUES 
    ('agent', (SELECT entity_id FROM entities WHERE name = 'optimizer_agent'), 
     'capability', 'Enable self-optimization for the optimizer agent itself', 
     'high', 0.95, 'pending', 
     json_object('recursive_improvement', true, 'phase', 7)),
    
    ('process', 0, 
     'automation', 'Automate improvement deployment process', 
     'high', 0.9, 'pending', 
     json_object('process_name', 'improvement_deployment', 'phase', 7)),
    
    ('system', 0, 
     'monitoring', 'Create real-time improvement dashboard', 
     'medium', 0.85, 'pending', 
     json_object('dashboard_type', 'self_improvement_metrics', 'phase', 7));