-- Migration 001: Add Entity Framework Tables
-- This migration adds the new entity-based architecture tables alongside existing tables
-- Phase 1 of the system update plan

-- 1. Core Entity Tables

-- Entity metadata table (tracks all entities in the system)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('agent', 'task', 'process', 'tool', 'document', 'event')),
    entity_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_task_id INTEGER,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'deprecated', 'testing')),
    metadata TEXT, -- JSON object
    UNIQUE(entity_type, entity_id),
    FOREIGN KEY (created_by_task_id) REFERENCES tasks(id)
);

-- Entity relationships table
CREATE TABLE IF NOT EXISTS entity_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN ('uses', 'depends_on', 'creates', 'optimizes', 'triggers', 'references', 'contains', 'inherits')),
    strength REAL DEFAULT 1.0 CHECK(strength >= 0 AND strength <= 1),
    context TEXT, -- JSON object
    created_by_event_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_event_id) REFERENCES events(id)
);

-- 2. Process Tables

-- Process templates table
CREATE TABLE IF NOT EXISTS processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    template TEXT NOT NULL, -- JSON array of process steps
    parameters_schema TEXT NOT NULL, -- JSON schema
    success_criteria TEXT, -- JSON array
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    average_execution_time REAL DEFAULT 0.0,
    version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_task_id INTEGER,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'deprecated', 'testing')),
    FOREIGN KEY (created_by_task_id) REFERENCES tasks(id)
);

-- Process instances table (tracks process executions)
CREATE TABLE IF NOT EXISTS process_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    parameters TEXT NOT NULL, -- JSON object
    state TEXT NOT NULL, -- JSON object tracking execution state
    current_step_id TEXT,
    status TEXT NOT NULL DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_seconds REAL,
    error_message TEXT,
    FOREIGN KEY (process_id) REFERENCES processes(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- 3. Enhanced Event System Tables

-- Events table (comprehensive event tracking)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    primary_entity_type TEXT NOT NULL,
    primary_entity_id INTEGER NOT NULL,
    related_entities TEXT, -- JSON object {entity_type: [entity_ids]}
    event_data TEXT, -- JSON object
    outcome TEXT CHECK(outcome IN ('success', 'failure', 'partial', 'error', 'timeout')),
    tree_id INTEGER,
    parent_event_id INTEGER,
    duration_seconds REAL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON object
    FOREIGN KEY (parent_event_id) REFERENCES events(id)
);

-- 4. Review and Counter Tables

-- Rolling review counters
CREATE TABLE IF NOT EXISTS rolling_review_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    counter_type TEXT NOT NULL CHECK(counter_type IN ('usage', 'creation', 'modification', 'error', 'success', 'failure')),
    count INTEGER DEFAULT 0,
    threshold INTEGER NOT NULL,
    last_review_at TIMESTAMP,
    next_review_due TIMESTAMP,
    review_frequency TEXT NOT NULL DEFAULT 'threshold' CHECK(review_frequency IN ('threshold', 'periodic', 'hybrid')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_id, counter_type)
);

-- Optimization opportunities table
CREATE TABLE IF NOT EXISTS optimization_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    opportunity_type TEXT NOT NULL,
    description TEXT NOT NULL,
    potential_impact REAL DEFAULT 0.0,
    effort_estimate TEXT CHECK(effort_estimate IN ('low', 'medium', 'high')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'rejected')),
    created_by_event_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT,
    FOREIGN KEY (created_by_event_id) REFERENCES events(id)
);

-- Entity effectiveness tracking
CREATE TABLE IF NOT EXISTS entity_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_id INTEGER,
    context TEXT, -- JSON object
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- 5. Performance Indexes

-- Entity indexes
CREATE INDEX IF NOT EXISTS idx_entities_type_id ON entities(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_created_by ON entities(created_by_task_id);

-- Entity relationship indexes
CREATE INDEX IF NOT EXISTS idx_entity_relationships_source ON entity_relationships(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_target ON entity_relationships(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_type ON entity_relationships(relationship_type);

-- Process indexes
CREATE INDEX IF NOT EXISTS idx_processes_category ON processes(category);
CREATE INDEX IF NOT EXISTS idx_processes_status ON processes(status);
CREATE INDEX IF NOT EXISTS idx_process_instances_process ON process_instances(process_id);
CREATE INDEX IF NOT EXISTS idx_process_instances_task ON process_instances(task_id);
CREATE INDEX IF NOT EXISTS idx_process_instances_status ON process_instances(status);

-- Event indexes
CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(primary_entity_type, primary_entity_id);
CREATE INDEX IF NOT EXISTS idx_events_tree_id ON events(tree_id);
CREATE INDEX IF NOT EXISTS idx_events_parent ON events(parent_event_id);
CREATE INDEX IF NOT EXISTS idx_events_outcome ON events(outcome);

-- Review counter indexes
CREATE INDEX IF NOT EXISTS idx_review_counters_entity ON rolling_review_counters(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_review_counters_due ON rolling_review_counters(next_review_due);

-- Optimization indexes
CREATE INDEX IF NOT EXISTS idx_optimization_entity ON optimization_opportunities(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_optimization_status ON optimization_opportunities(status);

-- Effectiveness indexes
CREATE INDEX IF NOT EXISTS idx_effectiveness_entity ON entity_effectiveness(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_effectiveness_metric ON entity_effectiveness(metric_name);
CREATE INDEX IF NOT EXISTS idx_effectiveness_time ON entity_effectiveness(measured_at);

-- 6. Views for Analytics

-- Entity usage statistics view
CREATE VIEW IF NOT EXISTS entity_usage_stats AS
SELECT 
    e.entity_type,
    e.entity_id,
    e.name,
    COUNT(DISTINCT ev.id) as total_events,
    COUNT(DISTINCT CASE WHEN ev.outcome = 'success' THEN ev.id END) as success_count,
    COUNT(DISTINCT CASE WHEN ev.outcome = 'failure' THEN ev.id END) as failure_count,
    AVG(CASE WHEN ev.outcome = 'success' THEN 1.0 ELSE 0.0 END) as success_rate,
    MAX(ev.timestamp) as last_used,
    AVG(ev.duration_seconds) as avg_duration
FROM entities e
LEFT JOIN events ev ON ev.primary_entity_type = e.entity_type 
    AND ev.primary_entity_id = e.entity_id
    AND ev.timestamp > datetime('now', '-30 days')
GROUP BY e.entity_type, e.entity_id, e.name;

-- Process effectiveness view
CREATE VIEW IF NOT EXISTS process_effectiveness AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.usage_count,
    p.success_rate,
    p.average_execution_time,
    COUNT(DISTINCT pi.id) as recent_executions,
    AVG(CASE WHEN pi.status = 'completed' THEN 1.0 ELSE 0.0 END) as recent_success_rate,
    AVG(pi.execution_time_seconds) as recent_avg_duration
FROM processes p
LEFT JOIN process_instances pi ON pi.process_id = p.id 
    AND pi.started_at > datetime('now', '-7 days')
GROUP BY p.id;

-- Entity relationship graph view
CREATE VIEW IF NOT EXISTS entity_relationship_graph AS
SELECT 
    er.source_type,
    er.source_id,
    e1.name as source_name,
    er.relationship_type,
    er.target_type,
    er.target_id,
    e2.name as target_name,
    er.strength,
    COUNT(*) OVER (PARTITION BY er.source_type, er.source_id) as outgoing_connections,
    COUNT(*) OVER (PARTITION BY er.target_type, er.target_id) as incoming_connections
FROM entity_relationships er
LEFT JOIN entities e1 ON e1.entity_type = er.source_type AND e1.entity_id = er.source_id
LEFT JOIN entities e2 ON e2.entity_type = er.target_type AND e2.entity_id = er.target_id;

-- Review triggers view
CREATE VIEW IF NOT EXISTS review_triggers AS
SELECT 
    rrc.entity_type,
    rrc.entity_id,
    e.name as entity_name,
    rrc.counter_type,
    rrc.count,
    rrc.threshold,
    CAST(rrc.count AS FLOAT) / rrc.threshold as completion_ratio,
    rrc.last_review_at,
    rrc.next_review_due,
    CASE 
        WHEN rrc.review_frequency = 'threshold' AND rrc.count >= rrc.threshold THEN 1
        WHEN rrc.review_frequency = 'periodic' AND datetime('now') >= rrc.next_review_due THEN 1
        WHEN rrc.review_frequency = 'hybrid' AND (rrc.count >= rrc.threshold OR datetime('now') >= rrc.next_review_due) THEN 1
        ELSE 0
    END as needs_review
FROM rolling_review_counters rrc
LEFT JOIN entities e ON e.entity_type = rrc.entity_type AND e.entity_id = rrc.entity_id
ORDER BY needs_review DESC, completion_ratio DESC;