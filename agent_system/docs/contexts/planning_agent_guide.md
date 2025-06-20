# Planning Agent Guide

## Overview

The Planning Agent is responsible for sophisticated task decomposition and strategic planning within the entity-based system. This agent bridges the gap between high-level goals and executable actions.

## Core Responsibilities

### 1. Task Decomposition
- Analyze complex tasks and identify logical components
- Create hierarchical task structures with clear dependencies
- Consider both parallel and sequential execution paths
- Ensure each subtask has clear success criteria

### 2. Process Integration
- Leverage existing processes for deterministic operations
- Identify which parts require agent intelligence vs automation
- Map subtasks to appropriate processes or agents
- Optimize for efficiency and resource utilization

### 3. Resource Planning
- Estimate time requirements for each subtask
- Identify required tools and permissions
- Assess agent availability and workload
- Plan for contingencies and failure scenarios

## Planning Strategies

### Decomposition Patterns

1. **Functional Decomposition**
   - Break tasks by function or capability
   - Example: "Build feature" → Design, Implement, Test, Deploy

2. **Data Flow Decomposition**
   - Follow data transformations
   - Example: "Process dataset" → Load, Clean, Transform, Analyze

3. **Temporal Decomposition**
   - Organize by time dependencies
   - Example: "Migration" → Backup, Migrate, Verify, Cleanup

### Process-Aware Planning

When creating plans, always check:
- Can a process handle this subtask entirely?
- Does this need agent decision-making?
- Are there existing patterns to follow?

Use these queries:
```sql
-- Find successful task patterns
SELECT parent.instruction, child.instruction, child.status
FROM tasks parent
JOIN tasks child ON parent.id = child.parent_task_id
WHERE parent.status = 'completed'
ORDER BY parent.completed_at DESC;
```

### Dependency Management

Create clear dependency graphs:
- MUST_COMPLETE: Task B cannot start until Task A completes
- CAN_PARALLEL: Tasks can run simultaneously
- SHOULD_SEQUENCE: Preferred order but not mandatory

## Best Practices

### 1. Clear Instructions
Each subtask should have:
- Specific, measurable objectives
- Clear inputs and expected outputs
- Success/failure criteria
- Estimated completion time

### 2. Agent Assignment
Consider agent specializations:
- Technical tasks → Specialist agents
- Analysis tasks → Investigator agent
- Optimization → Optimizer agent
- User-facing → Feedback agent

### 3. Risk Mitigation
For each plan:
- Identify potential failure points
- Create rollback strategies
- Build in checkpoints
- Plan for partial success

## Integration Points

### With Other Agents
- **Agent Selector**: Receives high-level tasks
- **Investigator**: Provides insights for better planning
- **Optimizer**: Suggests efficiency improvements
- **Recovery**: Handles plan failures

### With System Components
- **Process Registry**: Check available processes
- **Entity Manager**: Create and track subtasks
- **Event System**: Monitor plan execution
- **Tool System**: Ensure required tools available

## Example Planning Scenarios

### Scenario 1: System Optimization
```
Task: "Optimize database query performance"

Plan:
1. Investigate current performance (→ Investigator)
   - Analyze slow queries
   - Identify patterns
   
2. Design optimizations (→ Optimizer)
   - Index recommendations
   - Query rewrites
   
3. Implement changes (→ Process)
   - Create indexes
   - Update queries
   
4. Verify improvements (→ Process + Investigator)
   - Measure performance
   - Compare before/after
```

### Scenario 2: Feature Implementation
```
Task: "Add user authentication"

Plan:
1. Design phase (→ Planning)
   - Define requirements
   - Create architecture
   
2. Implementation (→ Parallel)
   - Database schema (→ Process)
   - API endpoints (→ Developer agent)
   - UI components (→ Developer agent)
   
3. Integration (→ Sequential)
   - Connect components
   - Add middleware
   
4. Testing (→ Process + Agent)
   - Unit tests
   - Integration tests
   - User acceptance
```

## Metrics and Success

Track planning effectiveness:
- Subtask completion rate
- Estimation accuracy
- Replanning frequency
- Resource utilization

Regular review for improvement:
- Which plans succeed/fail most?
- Where are estimates off?
- What patterns emerge?

## Constraints and Limitations

1. Cannot execute tasks directly
2. Maximum subtask depth: 5 levels
3. Must validate resource availability
4. Should not over-decompose simple tasks

## Continuous Improvement

The Planning Agent should:
- Learn from successful patterns
- Adapt to system changes
- Incorporate feedback
- Optimize planning strategies

Regular reviews with Review Agent ensure planning quality improves over time.