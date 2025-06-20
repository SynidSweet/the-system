-- Phase 6: Context Documents for New Agents
-- This migration adds the specialized context documents referenced by Phase 6 agents

-- Planning Agent Guide
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'planning_agent_guide',
    'Planning Agent Guide',
    '# Planning Agent Guide

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

[Full content available in planning_agent_guide.md]',
    'agent_guide',
    json_array('planning', 'decomposition', 'process', 'phase6'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Investigator Agent Guide
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'investigator_agent_guide',
    'Investigator Agent Guide',
    '# Investigator Agent Guide

## Overview

The Investigator Agent specializes in pattern analysis, root cause investigation, and hypothesis-driven problem solving. This agent acts as the system''s detective, uncovering insights from data and events.

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

[Full content available in investigator_agent_guide.md]',
    'agent_guide',
    json_array('investigation', 'analysis', 'patterns', 'phase6'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Optimizer Agent Guide
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'optimizer_agent_guide',
    'Optimizer Agent Guide',
    '# Optimizer Agent Guide

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

[Full content available in optimizer_agent_guide.md]',
    'agent_guide',
    json_array('optimization', 'performance', 'efficiency', 'phase6'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Recovery Agent Guide
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'recovery_agent_guide',
    'Recovery Agent Guide',
    '# Recovery Agent Guide

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

[Full content available in recovery_agent_guide.md]',
    'agent_guide',
    json_array('recovery', 'error_handling', 'resilience', 'phase6'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Feedback Agent Guide
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'feedback_agent_guide',
    'Feedback Agent Guide',
    '# Feedback Agent Guide

## Overview

The Feedback Agent serves as the primary interface for user interaction, feedback collection, and communication. This agent ensures that user input is properly processed, routed, and acted upon while maintaining a positive user experience.

## Core Responsibilities

### 1. User Communication
- Interact professionally with users
- Provide clear status updates
- Set appropriate expectations
- Deliver helpful responses

### 2. Feedback Processing
- Collect user feedback
- Categorize input appropriately
- Extract actionable items
- Route to relevant agents

### 3. Follow-up Management
- Track feedback status
- Provide progress updates
- Close feedback loops
- Ensure user satisfaction

[Full content available in feedback_agent_guide.md]',
    'agent_guide',
    json_array('feedback', 'user_interaction', 'communication', 'phase6'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Performance Guide (referenced by optimizer)
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'performance_guide',
    'System Performance Guide',
    '# System Performance Guide

## Overview
This guide provides comprehensive information about system performance monitoring, analysis, and optimization strategies.

## Key Performance Indicators

### Response Time Metrics
- Average task completion time
- 95th percentile response time
- Tool execution latency
- Agent processing time

### Throughput Metrics
- Tasks per hour
- Events processed per minute
- Concurrent task capacity
- Tool call rate

### Resource Utilization
- Database query efficiency
- Memory usage patterns
- API call frequency
- Storage growth rate

## Performance Analysis Tools

### SQL Performance Queries
- Slow query identification
- Index usage analysis
- Table scan detection
- Query plan examination

### Event Pattern Analysis
- Peak usage times
- Bottleneck identification
- Failure correlation
- Resource contention

## Optimization Strategies

### Database Optimization
- Index creation
- Query rewriting
- Connection pooling
- Cache implementation

### Process Optimization
- Parallel execution
- Batch processing
- Async operations
- Resource pooling

### Agent Optimization
- Context reduction
- Tool selection
- Prompt engineering
- Model selection',
    'guide',
    json_array('performance', 'optimization', 'monitoring'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Error Handling Guide (referenced by recovery)
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'error_handling_guide',
    'Error Handling and Recovery Guide',
    '# Error Handling and Recovery Guide

## Overview
This guide covers error detection, classification, handling strategies, and recovery procedures for maintaining system stability.

## Error Classification

### Transient Errors
- Network timeouts
- Temporary resource unavailability
- Rate limiting
- Concurrency conflicts

### System Errors
- Service failures
- Database connection issues
- Memory exhaustion
- Process crashes

### Data Errors
- Validation failures
- Constraint violations
- Data corruption
- State inconsistency

### Logic Errors
- Infinite loops
- Deadlocks
- Race conditions
- Invalid operations

## Recovery Strategies

### Retry Mechanisms
- Exponential backoff
- Circuit breakers
- Retry limits
- Jitter implementation

### Rollback Procedures
- Transaction rollback
- State restoration
- Change reversal
- Checkpoint recovery

### Failover Strategies
- Service redundancy
- Load balancing
- Health checks
- Automatic failover

## Best Practices

### Error Prevention
- Input validation
- Defensive programming
- Resource limits
- Timeout configuration

### Error Detection
- Health monitoring
- Log analysis
- Metric alerts
- Anomaly detection

### Error Response
- Graceful degradation
- Error isolation
- Clear messaging
- Incident logging',
    'guide',
    json_array('error_handling', 'recovery', 'resilience'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- User Interaction Guide (referenced by feedback)
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'user_interaction_guide',
    'User Interaction and Communication Guide',
    '# User Interaction and Communication Guide

## Overview
This guide establishes best practices for user communication, feedback handling, and maintaining positive user relationships.

## Communication Principles

### Clarity
- Use simple language
- Avoid technical jargon
- Provide context
- Be specific

### Empathy
- Acknowledge concerns
- Show understanding
- Validate experiences
- Offer support

### Responsiveness
- Timely acknowledgment
- Regular updates
- Clear timelines
- Proactive communication

### Professionalism
- Courteous tone
- Respectful language
- Solution-focused
- Consistent messaging

## Feedback Categories

### Bug Reports
- System errors
- Unexpected behavior
- Performance issues
- Data problems

### Feature Requests
- New functionality
- Enhancements
- Integrations
- Workflow improvements

### Support Requests
- How-to questions
- Clarifications
- Best practices
- Training needs

## Response Templates

### Initial Acknowledgment
- Thank user
- Confirm receipt
- Provide reference number
- Set expectations

### Status Updates
- Current progress
- Next steps
- Timeline updates
- Any blockers

### Resolution Notice
- Solution summary
- Impact explanation
- Additional resources
- Satisfaction check

## Best Practices

### Active Listening
- Read carefully
- Ask clarifications
- Confirm understanding
- Show engagement

### Expectation Management
- Be realistic
- Communicate constraints
- Provide alternatives
- Update regularly

### Relationship Building
- Personal touch
- Remember context
- Follow through
- Show appreciation',
    'guide',
    json_array('user_interaction', 'communication', 'feedback'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Recovery Procedures (referenced by recovery agent)
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'recovery_procedures',
    'System Recovery Procedures',
    '# System Recovery Procedures

## Overview
Detailed procedures for recovering from various system failures and maintaining operational continuity.

## Recovery Playbooks

### Task Recovery
1. Identify stuck/failed tasks
2. Assess task state and history
3. Determine recovery strategy
4. Execute recovery
5. Verify completion
6. Document incident

### Service Recovery
1. Detect service failure
2. Attempt automatic restart
3. Check service health
4. Escalate if needed
5. Monitor stability
6. Update runbooks

### Data Recovery
1. Identify data issues
2. Assess corruption extent
3. Restore from backup
4. Validate integrity
5. Reconcile differences
6. Prevent recurrence

### State Recovery
1. Detect invalid state
2. Identify last good state
3. Rollback changes
4. Restore consistency
5. Verify operations
6. Update safeguards

## Emergency Procedures

### Critical Failure Response
- Immediate assessment
- Stakeholder notification
- Service isolation
- Recovery initiation
- Progress tracking
- Post-mortem planning

### Data Loss Prevention
- Stop writes
- Backup current state
- Assess damage
- Recovery planning
- Careful restoration
- Verification process

## Rollback Procedures

### Code Rollback
- Identify breaking change
- Revert to previous version
- Verify functionality
- Investigate root cause
- Plan proper fix
- Deploy with care

### Configuration Rollback
- Document current config
- Restore previous config
- Test functionality
- Monitor behavior
- Update documentation
- Review change process',
    'procedures',
    json_array('recovery', 'rollback', 'emergency', 'procedures'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Feedback Handling Procedures (referenced by feedback agent)
INSERT INTO context_documents (id, name, title, content, category, tags, version, format, created_at, updated_at)
VALUES (
    (SELECT COALESCE(MAX(id), 0) + 1 FROM context_documents),
    'feedback_handling_procedures',
    'Feedback Handling Procedures',
    '# Feedback Handling Procedures

## Overview
Standard operating procedures for collecting, processing, and responding to user feedback.

## Feedback Collection

### Channels
- Direct messages
- Support tickets
- Feature requests
- Bug reports
- General comments

### Initial Processing
1. Acknowledge receipt
2. Assign reference number
3. Categorize feedback
4. Assess priority
5. Route appropriately
6. Set expectations

## Categorization Framework

### Priority Levels
- **Critical**: System breaking, data loss risk
- **High**: Major functionality impact
- **Medium**: Important but not urgent
- **Low**: Nice to have, minor issues

### Type Classification
- **Bug**: Something broken
- **Feature**: New capability request
- **Enhancement**: Improvement to existing
- **Question**: Needs clarification
- **Complaint**: Dissatisfaction

## Response Workflows

### Bug Report Workflow
1. Reproduce issue
2. Assess impact
3. Route to recovery/investigator
4. Track resolution
5. Test fix
6. Notify user

### Feature Request Workflow
1. Understand use case
2. Assess feasibility
3. Route to planning
4. Get estimation
5. Prioritize
6. Update requester

### Support Request Workflow
1. Understand question
2. Search knowledge base
3. Provide answer
4. Verify understanding
5. Document if new
6. Follow up

## Communication Standards

### Response Times
- Initial: Within 1 hour
- Update: Every 24-48 hours
- Resolution: Immediate notification
- Follow-up: Within 1 week

### Message Tone
- Professional
- Empathetic
- Solution-focused
- Clear and concise

### Status Updates
- What''s been done
- What''s happening now
- What''s next
- Expected timeline

## Metrics and Tracking

### Key Metrics
- Response time
- Resolution time
- User satisfaction
- Feedback volume
- Category distribution

### Quality Checks
- Response accuracy
- User satisfaction
- Issue recurrence
- Process efficiency',
    'procedures',
    json_array('feedback', 'support', 'communication', 'procedures'),
    '1.0.0',
    'markdown',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Add Phase 6 agents to agent_registry document
UPDATE context_documents
SET content = content || '

## Phase 6 Agents (New Specialized Agents)

### Planning Agent
- **Specialization**: Sophisticated task decomposition and planning
- **Key Features**: Process-aware planning, dependency management, resource estimation
- **Tools**: break_down_task, start_subtask, entity_manager, sql_lite
- **Integration**: Coordinates with all other specialist agents

### Investigator Agent
- **Specialization**: Pattern analysis and root cause investigation
- **Key Features**: Hypothesis testing, correlation analysis, evidence-based conclusions
- **Tools**: sql_lite, entity_manager, file_system
- **Use Cases**: Failure analysis, performance investigation, anomaly detection

### Optimizer Agent
- **Specialization**: System performance and efficiency optimization
- **Key Features**: A/B testing, incremental improvements, data-driven decisions
- **Tools**: sql_lite, entity_manager, message_user
- **Focus**: Query optimization, workflow efficiency, resource utilization

### Recovery Agent
- **Specialization**: Error handling and system recovery
- **Key Features**: Automatic recovery, rollback procedures, health monitoring
- **Tools**: entity_manager, terminal, sql_lite, flag_for_review
- **Priority**: System stability and data integrity

### Feedback Agent
- **Specialization**: User interaction and feedback processing
- **Key Features**: Professional communication, feedback routing, loop closure
- **Tools**: message_user, entity_manager, start_subtask
- **Focus**: User satisfaction and actionable feedback',
updated_at = CURRENT_TIMESTAMP
WHERE name = 'agent_registry';