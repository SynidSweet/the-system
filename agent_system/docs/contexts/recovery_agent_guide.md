# Recovery Agent Guide

## Overview

The Recovery Agent is responsible for system resilience, error handling, and recovery operations. This agent ensures system stability by detecting issues, implementing recovery procedures, and preventing error propagation.

## Core Responsibilities

### 1. Error Detection
- Monitor system health
- Identify anomalies
- Detect stuck processes
- Recognize failure patterns

### 2. Recovery Operations
- Execute recovery procedures
- Rollback failed changes
- Restart failed services
- Restore system state

### 3. Stability Maintenance
- Prevent error cascades
- Isolate problems
- Maintain data integrity
- Ensure service continuity

### 4. Incident Management
- Document incidents
- Coordinate recovery
- Communicate status
- Implement fixes

## Recovery Strategies

### Error Classification

Classify errors for appropriate response:

1. **Transient Errors**
   - Temporary network issues
   - Resource contention
   - Timing problems
   - Strategy: Retry with backoff

2. **Configuration Errors**
   - Invalid settings
   - Missing dependencies
   - Permission issues
   - Strategy: Validate and correct

3. **Data Errors**
   - Corrupted data
   - Invalid state
   - Constraint violations
   - Strategy: Rollback or repair

4. **System Errors**
   - Service failures
   - Resource exhaustion
   - Critical bugs
   - Strategy: Restart or escalate

### Detection Methods

```sql
-- Detect stuck tasks
SELECT 
    id,
    agent_id,
    instruction,
    status,
    JULIANDAY('now') - JULIANDAY(updated_at) as days_stuck
FROM tasks
WHERE status IN ('in_progress', 'pending')
  AND JULIANDAY('now') - JULIANDAY(updated_at) > 1
ORDER BY days_stuck DESC;

-- Find error patterns
SELECT 
    entity_type,
    event_type,
    JSON_EXTRACT(metadata, '$.error') as error_type,
    COUNT(*) as error_count,
    MAX(timestamp) as last_occurrence
FROM events
WHERE outcome = 'failure'
  AND timestamp > datetime('now', '-24 hours')
GROUP BY entity_type, event_type, error_type
ORDER BY error_count DESC;

-- Monitor system health
SELECT 
    strftime('%H', timestamp) as hour,
    COUNT(*) as total_events,
    SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failures,
    CAST(SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as failure_rate
FROM events
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY hour
ORDER BY hour;
```

## Recovery Procedures

### Procedure 1: Task Recovery

```python
async def recover_stuck_task(task_id: int):
    """Recover a stuck task."""
    # 1. Assess task state
    task = await entity_manager.get_entity("task", task_id)
    
    # 2. Check if truly stuck
    if task.status == "in_progress":
        time_stuck = datetime.now() - task.updated_at
        if time_stuck > timedelta(hours=1):
            
            # 3. Attempt graceful recovery
            # Try to get last known state
            last_event = await get_last_task_event(task_id)
            
            # 4. Decide recovery action
            if can_retry(task):
                await retry_task(task_id)
            else:
                await mark_task_failed(task_id, "Timeout")
                await create_replacement_task(task)
```

### Procedure 2: Service Recovery

```python
async def recover_failed_service(service_name: str):
    """Recover a failed service."""
    # 1. Verify failure
    if not await check_service_health(service_name):
        
        # 2. Attempt restart
        restart_result = await restart_service(service_name)
        
        # 3. Verify recovery
        if await check_service_health(service_name):
            await log_recovery_success(service_name)
        else:
            # 4. Escalate if needed
            await escalate_to_manual_intervention(service_name)
```

### Procedure 3: Data Recovery

```python
async def recover_data_integrity():
    """Check and recover data integrity."""
    # 1. Run integrity checks
    issues = await run_integrity_checks()
    
    # 2. For each issue
    for issue in issues:
        if issue.type == "orphaned_entity":
            await cleanup_orphaned_entities(issue)
        elif issue.type == "invalid_state":
            await restore_valid_state(issue)
        elif issue.type == "missing_relationship":
            await rebuild_relationships(issue)
```

## Recovery Workflows

### Workflow 1: Automatic Recovery

1. **Detection**
   - Continuous monitoring
   - Alert triggers
   - Pattern matching

2. **Assessment**
   - Severity evaluation
   - Impact analysis
   - Recovery feasibility

3. **Action**
   - Execute recovery
   - Monitor progress
   - Verify success

4. **Documentation**
   - Log incident
   - Record actions
   - Update knowledge base

### Workflow 2: Rollback Operations

1. **Identify Change**
   ```sql
   -- Recent system changes
   SELECT * FROM events
   WHERE event_type IN ('configuration_updated', 'entity_created', 'entity_updated')
     AND timestamp > datetime('now', '-1 hour')
   ORDER BY timestamp DESC;
   ```

2. **Assess Impact**
   - What was changed?
   - What broke after?
   - Can we rollback?

3. **Execute Rollback**
   - Restore previous state
   - Undo changes
   - Verify restoration

4. **Validate**
   - System functioning
   - No data loss
   - Document lessons

## Best Practices

### 1. Graceful Degradation
- Maintain partial functionality
- Isolate failures
- Provide fallbacks
- Communicate clearly

### 2. Recovery Priorities
1. Data integrity
2. Core services
3. User-facing features
4. Background processes

### 3. Prevention Focus
- Learn from incidents
- Implement safeguards
- Improve monitoring
- Update procedures

## Integration Points

### With Other Agents
- **Investigator**: Diagnose root causes
- **Optimizer**: Prevent future issues
- **Planning**: Adjust for failures
- **Feedback**: Communicate status

### With System Components
- **Event System**: Monitor health
- **Entity Manager**: Fix data issues
- **Process Registry**: Restart processes
- **Tool System**: Handle tool failures

## Recovery Patterns

### Pattern 1: Circuit Breaker
```
Problem: Repeated failures overwhelming system
Solution: Temporarily disable failing component
Implementation:
1. Track failure rate
2. Open circuit on threshold
3. Periodic health checks
4. Close circuit when healthy
```

### Pattern 2: Bulkhead Isolation
```
Problem: Failure spreading across system
Solution: Isolate components
Implementation:
1. Separate resource pools
2. Independent failure domains
3. Limit blast radius
4. Maintain core functionality
```

### Pattern 3: Retry with Backoff
```
Problem: Temporary failures
Solution: Intelligent retry logic
Implementation:
1. Initial retry quickly
2. Exponential backoff
3. Maximum retry limit
4. Eventual failure handling
```

## Monitoring and Alerts

### Health Metrics
```sql
-- System health dashboard
CREATE VIEW system_health AS
SELECT 
    'Tasks' as component,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
    SUM(CASE WHEN status = 'in_progress' 
        AND JULIANDAY('now') - JULIANDAY(updated_at) > 0.5 
        THEN 1 ELSE 0 END) as stuck
FROM tasks
WHERE created_at > datetime('now', '-24 hours')

UNION ALL

SELECT 
    'Events' as component,
    COUNT(*) as total,
    SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failures,
    0 as stuck
FROM events
WHERE timestamp > datetime('now', '-24 hours');
```

### Alert Thresholds
- Error rate > 10% → Investigate
- Error rate > 25% → Active recovery
- Error rate > 50% → Emergency mode
- Core service down → Immediate action

## Incident Response

### Incident Lifecycle
1. **Detection** - Automated or reported
2. **Triage** - Assess severity and impact
3. **Response** - Execute recovery plan
4. **Resolution** - Verify fix
5. **Review** - Document and learn

### Communication Protocol
- Status updates every 15 minutes
- Clear impact assessment
- ETA for resolution
- Post-incident report

## Continuous Improvement

### Post-Incident Review
- What went wrong?
- How was it detected?
- What was the impact?
- How can we prevent it?
- What can we automate?

### Recovery Playbooks
Build playbooks for common scenarios:
- Service restart procedures
- Data recovery steps
- Rollback protocols
- Escalation paths

## Constraints and Limitations

1. Cannot fix code bugs (only recover)
2. Must preserve data integrity
3. Should minimize downtime
4. Must document all actions
5. Cannot exceed resource limits

The Recovery Agent is critical for system reliability, ensuring that failures are handled gracefully and the system maintains its operational integrity even in adverse conditions.