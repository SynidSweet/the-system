# Optimizer Agent Guide

## Overview

The Optimizer Agent focuses on improving system performance, efficiency, and effectiveness through data-driven optimization strategies. This agent identifies bottlenecks, recommends improvements, and validates optimization results.

## Core Responsibilities

### 1. Performance Optimization
- Identify performance bottlenecks
- Optimize query execution
- Improve agent efficiency
- Reduce resource consumption

### 2. Process Optimization
- Streamline workflows
- Eliminate redundancies
- Automate repetitive tasks
- Improve task routing

### 3. Configuration Tuning
- Optimize agent parameters
- Adjust system settings
- Fine-tune tool configurations
- Balance trade-offs

### 4. A/B Testing Framework
- Design experiments
- Implement test variations
- Measure results
- Roll out improvements

## Optimization Strategies

### Performance Analysis

Key metrics to monitor:
```sql
-- Agent performance metrics
SELECT 
    agent_type,
    COUNT(*) as task_count,
    AVG(JULIANDAY(completed_at) - JULIANDAY(created_at)) * 24 * 60 as avg_minutes,
    MIN(JULIANDAY(completed_at) - JULIANDAY(created_at)) * 24 * 60 as min_minutes,
    MAX(JULIANDAY(completed_at) - JULIANDAY(created_at)) * 24 * 60 as max_minutes,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failure_count
FROM tasks
WHERE created_at > datetime('now', '-7 days')
GROUP BY agent_type
ORDER BY avg_minutes DESC;

-- Tool usage efficiency
SELECT 
    tool_name,
    COUNT(*) as usage_count,
    AVG(execution_time_ms) as avg_time,
    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
    SUM(execution_time_ms) as total_time_ms
FROM tool_usage_events
WHERE timestamp > datetime('now', '-7 days')
GROUP BY tool_name
ORDER BY total_time_ms DESC;
```

### Bottleneck Identification

Common bottlenecks:
1. **Sequential Dependencies**
   - Tasks waiting on others
   - Could be parallelized
   - Resource locks

2. **Inefficient Queries**
   - Missing indexes
   - Full table scans
   - Redundant queries

3. **Resource Constraints**
   - Tool timeouts
   - Memory limits
   - API rate limits

### Optimization Techniques

#### 1. Query Optimization
```sql
-- Find slow queries
SELECT 
    operation,
    parameters,
    execution_time_ms,
    result_summary
FROM tool_usage_events
WHERE tool_name = 'sql_lite'
  AND execution_time_ms > 1000
ORDER BY execution_time_ms DESC
LIMIT 20;
```

Optimization actions:
- Add appropriate indexes
- Rewrite inefficient queries
- Implement query caching
- Batch similar operations

#### 2. Workflow Optimization
- Identify repeated patterns
- Create reusable processes
- Eliminate unnecessary steps
- Optimize task ordering

#### 3. Agent Optimization
- Reduce context size
- Streamline instructions
- Remove unused tools
- Optimize prompts

## A/B Testing Implementation

### Test Design
1. **Hypothesis Formation**
   - Clear improvement expectation
   - Measurable outcomes
   - Controlled variables

2. **Test Configuration**
   ```python
   test_config = {
       "test_name": "optimized_prompt_test",
       "control": current_configuration,
       "variant": optimized_configuration,
       "metric": "execution_time",
       "sample_size": 100,
       "success_criteria": "20% improvement"
   }
   ```

3. **Result Analysis**
   ```sql
   -- Compare A/B test results
   SELECT 
       test_group,
       COUNT(*) as sample_size,
       AVG(metric_value) as avg_metric,
       STDDEV(metric_value) as stddev_metric
   FROM ab_test_results
   WHERE test_name = ?
   GROUP BY test_group;
   ```

## Optimization Workflows

### Workflow 1: Agent Performance Optimization

1. **Baseline Measurement**
   - Current performance metrics
   - Resource usage
   - Success rates

2. **Analysis**
   - Identify slow operations
   - Find failure patterns
   - Analyze resource usage

3. **Optimization Design**
   - Propose improvements
   - Estimate impact
   - Plan implementation

4. **Testing**
   - Implement A/B test
   - Monitor results
   - Validate improvements

5. **Rollout**
   - Deploy successful optimizations
   - Monitor for regressions
   - Document changes

### Workflow 2: System-Wide Optimization

1. **System Profiling**
   ```sql
   -- Overall system health
   SELECT 
       entity_type,
       COUNT(*) as total_events,
       SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_count,
       AVG(CASE WHEN execution_time_ms IS NOT NULL THEN execution_time_ms END) as avg_time
   FROM events
   WHERE timestamp > datetime('now', '-24 hours')
   GROUP BY entity_type;
   ```

2. **Bottleneck Analysis**
   - Query execution plans
   - Task dependency graphs
   - Resource utilization

3. **Optimization Plan**
   - Prioritize by impact
   - Consider dependencies
   - Estimate effort

## Best Practices

### 1. Data-Driven Decisions
- Base optimizations on metrics
- Measure before and after
- Track long-term trends
- Document assumptions

### 2. Incremental Improvements
- Small, measurable changes
- Easier to debug
- Lower risk
- Compound benefits

### 3. Holistic View
- Consider system-wide impact
- Watch for side effects
- Balance competing goals
- Maintain stability

## Integration Points

### With Other Agents
- **Investigator**: Provides performance insights
- **Planning**: Optimizes task decomposition
- **Recovery**: Ensures optimization safety
- **Review**: Validates improvements

### With System Components
- **Entity Manager**: Update configurations
- **Event System**: Track metrics
- **Process Registry**: Optimize processes
- **Tool System**: Improve tool usage

## Optimization Patterns

### Pattern 1: Cache Implementation
```
Problem: Repeated expensive operations
Solution: Implement caching layer
Steps:
1. Identify cacheable operations
2. Design cache strategy
3. Implement with TTL
4. Monitor hit rates
```

### Pattern 2: Batch Processing
```
Problem: Many small operations
Solution: Batch similar operations
Steps:
1. Group similar requests
2. Process in batches
3. Optimize batch size
4. Handle partial failures
```

### Pattern 3: Parallel Execution
```
Problem: Sequential independent tasks
Solution: Enable parallel processing
Steps:
1. Identify independent tasks
2. Implement parallel execution
3. Manage resources
4. Coordinate results
```

## Metrics and KPIs

### Performance Metrics
- Average execution time
- 95th percentile latency
- Throughput (tasks/hour)
- Resource utilization

### Quality Metrics
- Success rate
- Error frequency
- Rollback rate
- User satisfaction

### Efficiency Metrics
- Cost per task
- Resource efficiency
- Automation percentage
- Manual intervention rate

## Continuous Improvement

### Optimization Cycle
1. Measure current state
2. Identify opportunities
3. Design improvements
4. Test changes
5. Deploy successful optimizations
6. Monitor and iterate

### Knowledge Building
- Document successful optimizations
- Build optimization playbooks
- Share learnings
- Create optimization templates

## Constraints and Considerations

1. Maintain system stability
2. Preserve functionality
3. Consider user experience
4. Balance speed vs accuracy
5. Document all changes
6. Enable rollback capability

The Optimizer Agent drives continuous improvement, ensuring the system becomes more efficient, effective, and scalable over time through systematic, data-driven optimization.