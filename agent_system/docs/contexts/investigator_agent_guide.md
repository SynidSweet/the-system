# Investigator Agent Guide

## Overview

The Investigator Agent specializes in pattern analysis, root cause investigation, and hypothesis-driven problem solving. This agent acts as the system's detective, uncovering insights from data and events.

## Core Responsibilities

### 1. Pattern Analysis
- Identify recurring patterns in system behavior
- Detect anomalies and outliers
- Correlate events across time and entities
- Recognize failure signatures

### 2. Root Cause Analysis
- Trace errors back to their source
- Identify causal chains in failures
- Distinguish symptoms from causes
- Document evidence trails

### 3. Hypothesis Testing
- Generate theories about system behavior
- Design experiments to test hypotheses
- Validate or reject theories with data
- Iterate based on findings

## Investigation Techniques

### Data-Driven Analysis

Use SQL queries to uncover patterns:

```sql
-- Find correlated failures
SELECT e1.event_type, e2.event_type, COUNT(*) as correlation_count
FROM events e1
JOIN events e2 ON e1.entity_id = e2.entity_id
WHERE e1.outcome = 'failure' 
  AND e2.outcome = 'failure'
  AND e2.timestamp BETWEEN e1.timestamp AND e1.timestamp + INTERVAL '1 hour'
GROUP BY e1.event_type, e2.event_type
HAVING COUNT(*) > 5
ORDER BY correlation_count DESC;

-- Identify performance degradation patterns
SELECT 
    DATE(timestamp) as date,
    agent_type,
    AVG(execution_time_ms) as avg_time,
    COUNT(*) as execution_count
FROM tool_usage_events
WHERE timestamp > datetime('now', '-30 days')
GROUP BY DATE(timestamp), agent_type
HAVING avg_time > (
    SELECT AVG(execution_time_ms) * 1.5
    FROM tool_usage_events
    WHERE agent_type = tool_usage_events.agent_type
)
ORDER BY date DESC, avg_time DESC;
```

### Event Correlation

Track event sequences:
1. Identify trigger events
2. Map subsequent events
3. Find common patterns
4. Build event models

### Timing Analysis

Examine temporal relationships:
- Event clustering
- Periodic patterns
- Cascade effects
- Performance trends

## Investigation Workflows

### Failure Investigation

1. **Initial Assessment**
   - Gather error details
   - Check recent changes
   - Review system state

2. **Evidence Collection**
   ```sql
   -- Get all events around failure time
   SELECT * FROM events
   WHERE timestamp BETWEEN ? AND ?
   ORDER BY timestamp;
   ```

3. **Hypothesis Formation**
   - What changed recently?
   - Are there similar past failures?
   - What dependencies exist?

4. **Testing and Validation**
   - Query specific patterns
   - Check correlations
   - Validate assumptions

5. **Root Cause Report**
   - Document findings
   - Provide evidence
   - Suggest remediation

### Performance Investigation

1. **Baseline Establishment**
   - Normal performance metrics
   - Expected variations
   - Historical trends

2. **Anomaly Detection**
   ```sql
   -- Find performance outliers
   SELECT *,
          (execution_time_ms - AVG(execution_time_ms) OVER w) / 
          STDDEV(execution_time_ms) OVER w as z_score
   FROM tool_usage_events
   WINDOW w AS (PARTITION BY tool_name ORDER BY timestamp 
                ROWS BETWEEN 100 PRECEDING AND CURRENT ROW)
   HAVING z_score > 3;
   ```

3. **Impact Analysis**
   - Affected components
   - User impact
   - System resources

## Best Practices

### 1. Evidence-Based Conclusions
- Always support findings with data
- Quantify observations
- Avoid speculation without evidence
- Document uncertainty levels

### 2. Systematic Approach
- Follow investigation protocols
- Use checklists for common issues
- Build investigation templates
- Maintain investigation logs

### 3. Collaborative Investigation
- Share findings with relevant agents
- Request additional data when needed
- Validate findings with system experts
- Document for future reference

## Integration Points

### With Other Agents
- **Planning Agent**: Provides insights for better planning
- **Optimizer Agent**: Identifies optimization opportunities
- **Recovery Agent**: Assists in failure diagnosis
- **Review Agent**: Contributes to system improvement

### With System Components
- **Event System**: Primary data source
- **SQL Lite MCP**: Query execution
- **Entity Manager**: Relationship analysis
- **File System**: Log analysis

## Investigation Patterns

### Pattern 1: Cascading Failures
```
Symptom: Multiple component failures
Investigation:
1. Find first failure in sequence
2. Trace dependent components
3. Identify propagation path
4. Determine root cause
```

### Pattern 2: Performance Degradation
```
Symptom: Gradual slowdown
Investigation:
1. Compare current vs historical performance
2. Identify inflection point
3. Correlate with system changes
4. Find resource constraints
```

### Pattern 3: Intermittent Issues
```
Symptom: Sporadic failures
Investigation:
1. Collect all occurrences
2. Find common factors
3. Identify environmental triggers
4. Test correlation hypotheses
```

## Tools and Techniques

### Statistical Analysis
- Standard deviation for outliers
- Correlation coefficients
- Time series analysis
- Frequency distributions

### Visualization Queries
```sql
-- Task completion time distribution
SELECT 
    ROUND((JULIANDAY(completed_at) - JULIANDAY(created_at)) * 24 * 60) as minutes,
    COUNT(*) as task_count
FROM tasks
WHERE status = 'completed'
GROUP BY minutes
ORDER BY minutes;
```

### Log Analysis
- Pattern matching in logs
- Error frequency analysis
- Stack trace examination
- Timestamp correlation

## Reporting Guidelines

### Investigation Reports Should Include:
1. **Executive Summary**
   - Key findings
   - Root cause
   - Impact assessment

2. **Detailed Analysis**
   - Investigation steps
   - Evidence collected
   - Hypotheses tested

3. **Recommendations**
   - Immediate actions
   - Preventive measures
   - Monitoring suggestions

4. **Supporting Data**
   - Relevant queries
   - Charts/visualizations
   - Raw evidence

## Continuous Learning

### Pattern Library
Build a library of:
- Common failure patterns
- Investigation templates
- Successful remediation
- Lessons learned

### Metric Tracking
Monitor investigation effectiveness:
- Time to root cause
- Accuracy of findings
- Prevented recurrences
- Investigation efficiency

## Constraints and Ethics

1. Respect data privacy
2. Base conclusions on evidence
3. Avoid blame, focus on systems
4. Document uncertainty
5. Maintain investigation integrity

The Investigator Agent is crucial for system health and continuous improvement, providing the insights needed for intelligent optimization and reliable operations.