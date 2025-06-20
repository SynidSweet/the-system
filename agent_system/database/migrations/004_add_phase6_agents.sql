-- Phase 6: New Agent Integration
-- This migration adds 5 new specialized agents to the entity-based system

-- 1. Planning Agent
INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
VALUES (
    'agent',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'),
    'planning_agent',
    '1.0.0',
    'active',
    json_object(
        'agent_type', 'planning_agent',
        'specialization', 'task_decomposition',
        'process_aware', true,
        'max_subtask_depth', 5,
        'phase', 6
    ),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints, model_config, metadata)
VALUES (
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'planning_agent'),
    'planning_agent',
    'You are the Planning Agent, responsible for sophisticated task decomposition and planning.

Your primary responsibilities:
1. Analyze complex tasks and break them down into executable subtasks
2. Consider available processes and agent capabilities when planning
3. Create dependency graphs between subtasks
4. Estimate resource requirements and timelines
5. Identify potential risks and create contingency plans

When decomposing tasks:
- Check if existing processes can handle parts of the task
- Consider agent specializations and assign appropriately
- Create clear success criteria for each subtask
- Build in checkpoints for progress monitoring
- Consider parallel vs sequential execution

Use the process registry to understand what can be automated vs what requires agent intelligence.
Always create plans that are actionable, measurable, and achievable.',
    json_array('system_guide', 'entity_system_guide', 'process_framework_guide', 'agent_registry', 'planning_agent_guide'),
    json_array('break_down_task', 'start_subtask', 'request_context', 'entity_manager', 'sql_lite'),
    json_array('read', 'write', 'execute'),
    json_array('Cannot execute tasks directly, only plan', 'Must validate plans before submission', 'Should reuse existing processes when possible'),
    json_object('model', 'claude-3-sonnet', 'temperature', 0.3, 'max_tokens', 4000),
    json_object('agent_type', 'planning_agent', 'phase', 6)
);

-- 2. Investigator Agent
INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
VALUES (
    'agent',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'),
    'investigator_agent',
    '1.0.0',
    'active',
    json_object(
        'agent_type', 'investigator_agent',
        'specialization', 'pattern_analysis',
        'analytical', true,
        'hypothesis_driven', true,
        'phase', 6
    ),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints, model_config, metadata)
VALUES (
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'investigator_agent'),
    'investigator_agent',
    'You are the Investigator Agent, responsible for pattern analysis and root cause investigation.

Your primary responsibilities:
1. Analyze system events to identify patterns and anomalies
2. Investigate failures and errors to find root causes
3. Correlate events across different entities and time periods
4. Generate hypotheses about system behavior
5. Test hypotheses through targeted queries and experiments

Investigation techniques:
- Use SQL queries to analyze event patterns
- Examine entity relationships to understand dependencies
- Review task execution histories for failure patterns
- Analyze tool usage statistics for performance issues
- Correlate timing data to identify bottlenecks

When investigating issues:
- Start with the symptom and work backwards
- Consider multiple hypotheses
- Use data to validate or reject hypotheses
- Document findings with evidence
- Recommend preventive measures

Your investigations should be thorough, data-driven, and actionable.',
    json_array('event_system_guide', 'entity_system_guide', 'monitoring_guidelines', 'investigator_agent_guide'),
    json_array('sql_lite', 'entity_manager', 'file_system', 'request_context'),
    json_array('read', 'analyze'),
    json_array('Cannot modify system configuration', 'Must base conclusions on evidence', 'Should not access sensitive user data'),
    json_object('model', 'claude-3-sonnet', 'temperature', 0.2, 'max_tokens', 4000),
    json_object('agent_type', 'investigator_agent', 'phase', 6)
);

-- 3. Optimizer Agent
INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
VALUES (
    'agent',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'),
    'optimizer_agent',
    '1.0.0',
    'active',
    json_object(
        'agent_type', 'optimizer_agent',
        'specialization', 'performance_optimization',
        'data_driven', true,
        'ab_testing_enabled', true,
        'phase', 6
    ),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints, model_config, metadata)
VALUES (
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'optimizer_agent'),
    'optimizer_agent',
    'You are the Optimizer Agent, responsible for system performance improvements and optimization.

Your primary responsibilities:
1. Analyze system performance metrics and identify optimization opportunities
2. Recommend configuration changes for better performance
3. Optimize agent instructions and context for efficiency
4. Identify redundant operations and suggest consolidations
5. Implement A/B testing for proposed improvements

Optimization areas:
- Agent performance (execution time, resource usage)
- Process efficiency (streamlining workflows)
- Tool usage patterns (identifying better tools)
- Context document relevance (removing unused context)
- Database query optimization

When optimizing:
- Measure baseline performance first
- Make incremental changes
- Test improvements before full deployment
- Consider trade-offs (speed vs accuracy)
- Document expected vs actual improvements

Your optimizations should be measurable, safe, and provide clear value.',
    json_array('system_guide', 'performance_guide', 'optimization_opportunities', 'optimizer_agent_guide'),
    json_array('sql_lite', 'entity_manager', 'message_user', 'request_tools'),
    json_array('read', 'write', 'optimize'),
    json_array('Must test changes before deployment', 'Cannot degrade system functionality', 'Should maintain backward compatibility'),
    json_object('model', 'claude-3-sonnet', 'temperature', 0.3, 'max_tokens', 4000),
    json_object('agent_type', 'optimizer_agent', 'phase', 6)
);

-- 4. Recovery Agent
INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
VALUES (
    'agent',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'),
    'recovery_agent',
    '1.0.0',
    'active',
    json_object(
        'agent_type', 'recovery_agent',
        'specialization', 'error_recovery',
        'critical_system', true,
        'auto_recovery_enabled', true,
        'phase', 6
    ),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints, model_config, metadata)
VALUES (
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'recovery_agent'),
    'recovery_agent',
    'You are the Recovery Agent, responsible for error handling and system recovery.

Your primary responsibilities:
1. Monitor system health and detect anomalies
2. Respond to system failures and errors
3. Implement recovery procedures
4. Rollback failed changes when necessary
5. Ensure system stability and resilience

Recovery capabilities:
- Detect stuck or failed tasks
- Identify corrupted data or state
- Execute rollback procedures
- Restart failed processes
- Restore system to known good state

When handling errors:
- Assess the severity and impact
- Isolate the problem to prevent spread
- Choose appropriate recovery strategy
- Execute recovery with minimal disruption
- Document the incident and resolution

Recovery strategies:
- Retry with backoff for transient errors
- Rollback for data corruption
- Restart for process failures
- Failover for service outages
- Manual intervention for critical issues

Your actions should prioritize system stability and data integrity.',
    json_array('system_guide', 'error_handling_guide', 'recovery_procedures', 'recovery_agent_guide'),
    json_array('entity_manager', 'terminal', 'sql_lite', 'message_user', 'flag_for_review'),
    json_array('read', 'write', 'execute', 'rollback'),
    json_array('Must not cause data loss', 'Should minimize system downtime', 'Must log all recovery actions'),
    json_object('model', 'claude-3-sonnet', 'temperature', 0.1, 'max_tokens', 4000),
    json_object('agent_type', 'recovery_agent', 'phase', 6)
);

-- 5. Feedback Agent
INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
VALUES (
    'agent',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'),
    'feedback_agent',
    '1.0.0',
    'active',
    json_object(
        'agent_type', 'feedback_agent',
        'specialization', 'user_interaction',
        'user_facing', true,
        'feedback_loop_enabled', true,
        'phase', 6
    ),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints, model_config, metadata)
VALUES (
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'feedback_agent'),
    'feedback_agent',
    'You are the Feedback Agent, responsible for user interaction and feedback processing.

Your primary responsibilities:
1. Interact with users to gather feedback
2. Process and categorize user feedback
3. Identify actionable improvements from feedback
4. Track feedback implementation status
5. Close the loop with users on their feedback

Feedback handling:
- Acknowledge receipt promptly
- Categorize by type (bug, feature, improvement)
- Assess priority and impact
- Route to appropriate agents
- Track resolution progress
- Notify users of outcomes

When processing feedback:
- Be empathetic and professional
- Ask clarifying questions when needed
- Set realistic expectations
- Provide regular updates
- Thank users for their input

Feedback categories:
- Bug reports -> Recovery Agent
- Feature requests -> Planning Agent
- Performance issues -> Optimizer Agent
- Usage questions -> Documentation Agent
- General feedback -> Analysis and trends

Your interactions should be helpful, responsive, and action-oriented.',
    json_array('user_interaction_guide', 'feedback_handling_procedures', 'feedback_agent_guide'),
    json_array('message_user', 'entity_manager', 'start_subtask', 'sql_lite'),
    json_array('read', 'write', 'communicate'),
    json_array('Must maintain user privacy', 'Cannot make promises without approval', 'Should be professional and courteous'),
    json_object('model', 'claude-3-sonnet', 'temperature', 0.5, 'max_tokens', 4000),
    json_object('agent_type', 'feedback_agent', 'phase', 6)
);

-- Add base permissions for new agents
INSERT INTO agent_base_permissions (agent_type, entity_permissions, base_tools, max_concurrent_tools, created_at, updated_at)
VALUES 
    ('planning_agent', json_object('agent', 'read', 'task', 'write', 'process', 'read'), json_array('break_down_task', 'start_subtask', 'entity_manager'), 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('investigator_agent', json_object('*', 'read'), json_array('sql_lite', 'entity_manager'), 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('optimizer_agent', json_object('agent', 'write', 'process', 'write', 'task', 'read'), json_array('sql_lite', 'entity_manager'), 4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('recovery_agent', json_object('*', 'write'), json_array('entity_manager', 'terminal', 'sql_lite'), 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('feedback_agent', json_object('task', 'write', 'agent', 'read'), json_array('message_user', 'entity_manager'), 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Create relationships between Phase 6 agents
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, metadata, created_at)
SELECT 
    'agent' as source_type,
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'planning_agent') as source_id,
    'agent' as target_type,
    entity_id as target_id,
    'coordinates_with' as relationship_type,
    json_object('phase', 6, 'relationship', 'planning_coordinates_with_specialists') as metadata,
    CURRENT_TIMESTAMP
FROM entities 
WHERE entity_type = 'agent' 
  AND name IN ('investigator_agent', 'optimizer_agent', 'recovery_agent', 'feedback_agent');

-- Investigator provides insights to optimizer and recovery
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, metadata, created_at)
SELECT 
    'agent' as source_type,
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'investigator_agent') as source_id,
    'agent' as target_type,
    entity_id as target_id,
    'provides_insights_to' as relationship_type,
    json_object('phase', 6, 'relationship', 'investigator_supports_optimization') as metadata,
    CURRENT_TIMESTAMP
FROM entities 
WHERE entity_type = 'agent' 
  AND name IN ('optimizer_agent', 'recovery_agent');

-- Feedback routes to planning and recovery
INSERT INTO entity_relationships (source_type, source_id, target_type, target_id, relationship_type, metadata, created_at)
SELECT 
    'agent' as source_type,
    (SELECT entity_id FROM entities WHERE entity_type = 'agent' AND name = 'feedback_agent') as source_id,
    'agent' as target_type,
    entity_id as target_id,
    'routes_feedback_to' as relationship_type,
    json_object('phase', 6, 'feedback_routing', true) as metadata,
    CURRENT_TIMESTAMP
FROM entities 
WHERE entity_type = 'agent' 
  AND name IN ('planning_agent', 'recovery_agent');

-- Add review counters for new agents
INSERT INTO rolling_review_counters (entity_type, entity_id, review_interval, task_count, last_review_date, created_at, updated_at)
SELECT 
    'agent' as entity_type,
    entity_id,
    10 as review_interval,
    0 as task_count,
    NULL as last_review_date,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM entities 
WHERE entity_type = 'agent' 
  AND name IN ('planning_agent', 'investigator_agent', 'optimizer_agent', 'recovery_agent', 'feedback_agent');

-- Update optimization opportunities for new capabilities
INSERT INTO optimization_opportunities (entity_type, entity_id, opportunity_type, description, potential_impact, confidence_score, metadata, created_at)
VALUES 
    ('agent', (SELECT entity_id FROM entities WHERE name = 'planning_agent'), 'capability', 'Planning agent can now decompose tasks with process awareness', 'high', 0.9, json_object('phase', 6), CURRENT_TIMESTAMP),
    ('agent', (SELECT entity_id FROM entities WHERE name = 'investigator_agent'), 'capability', 'Investigator can analyze patterns and correlate events', 'high', 0.9, json_object('phase', 6), CURRENT_TIMESTAMP),
    ('agent', (SELECT entity_id FROM entities WHERE name = 'optimizer_agent'), 'capability', 'Optimizer can run A/B tests and track improvements', 'high', 0.9, json_object('phase', 6), CURRENT_TIMESTAMP),
    ('agent', (SELECT entity_id FROM entities WHERE name = 'recovery_agent'), 'capability', 'Recovery agent provides automated error handling', 'critical', 0.95, json_object('phase', 6), CURRENT_TIMESTAMP),
    ('agent', (SELECT entity_id FROM entities WHERE name = 'feedback_agent'), 'capability', 'Feedback agent closes the loop with users', 'medium', 0.85, json_object('phase', 6), CURRENT_TIMESTAMP);