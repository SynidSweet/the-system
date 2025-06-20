# Planning Agent Guide

## Overview

The Planning Agent is responsible for sophisticated task decomposition and strategic planning within the entity-based system, with a PRIMARY FOCUS on creating plans that maximize LLM agent effectiveness while minimizing unnecessary LLM calls. This agent bridges the gap between high-level goals and executable actions, strategically placing validation and verification points to catch pitfalls without bloating execution.

## Core Philosophy: LLM-Aware Planning

### Planning Principles for LLM Agents

1. **Strategic Validation Points**: Place checks at critical junctures, not everywhere
2. **Leverage Deterministic Steps**: Maximize use of code-based validation between LLM steps
3. **Batch Related Decisions**: Group similar LLM decisions to reduce calls
4. **Build in Error Recovery**: Plan for LLM mistakes without excessive redundancy
5. **Context Preservation**: Ensure each agent has sufficient context without overload

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

## LLM-Aware Planning Strategies

### Strategic Validation Placement

**Key Principle**: Validate at natural boundaries, not every step

1. **Critical Decision Points**
   - After major architectural decisions
   - Before irreversible operations
   - At phase transitions
   - When switching between agents

2. **Batch Validation Pattern**
   ```
   Bad: LLM → Validate → LLM → Validate → LLM → Validate
   Good: LLM → LLM → LLM → Comprehensive Validation → Recovery if needed
   ```

3. **Deterministic Checkpoints**
   - Use code-based validation wherever possible
   - Example: Schema validation, syntax checking, type verification
   - Reserve LLM validation for semantic/logical correctness

### Pitfall Prevention Strategies

1. **Common LLM Pitfalls to Plan For**
   - Hallucination of non-existent functions/files
   - Incomplete implementations
   - Inconsistent naming across subtasks
   - Lost context between steps

2. **Prevention Techniques**
   - **Context Anchoring**: Key information repeated at critical points
   - **Explicit Constraints**: Clear boundaries in each subtask
   - **Success Criteria**: Measurable, deterministic when possible
   - **Example Provision**: Include examples to guide LLM behavior

### Efficient LLM Utilization

1. **Task Bundling**
   - Group related small tasks for single LLM execution
   - Example: "Create model, validator, and tests" vs three separate tasks

2. **Progressive Elaboration**
   - Start with high-level plan
   - Detail only when necessary
   - Avoid over-planning uncertain paths

3. **Reusable Patterns**
   - Identify and document successful task patterns
   - Create templates for common operations
   - Reduce LLM reasoning for known patterns

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

## Best Practices for LLM Agent Planning

### 1. Clear Instructions with LLM Guidance
Each subtask should have:
- **Specific, measurable objectives** (with examples when helpful)
- **Clear inputs and expected outputs** (with types/schemas)
- **Success/failure criteria** (deterministic when possible)
- **Estimated completion time** (considering LLM processing)
- **Potential pitfalls** (specific to the task type)
- **Recovery instructions** (if validation fails)

### 2. Strategic Agent Assignment
Consider agent specializations AND validation needs:
- **Technical tasks → Specialist agents**
  - Validation: Code compilation, test execution
- **Analysis tasks → Investigator agent**
  - Validation: Data consistency checks
- **Optimization → Optimizer agent**  
  - Validation: Performance benchmarks
- **User-facing → Feedback agent**
  - Validation: Second opinion from review agent

### 3. LLM-Aware Risk Mitigation
For each plan:
- **Identify LLM-specific failure modes**
  - Incomplete code generation
  - Misunderstood requirements
  - Context loss between steps
- **Create smart checkpoints**
  - Not after every step
  - At natural phase boundaries
  - Before costly operations
- **Build in recovery paths**
  - Clear rollback instructions
  - Context restoration guidance
- **Plan for partial success**
  - How to salvage incomplete work
  - When to escalate vs retry

### 4. Validation Strategy Selection

Choose validation based on risk and cost:

1. **High Risk, High Cost → Second Opinion**
   - Architectural decisions
   - Data migrations
   - Security implementations

2. **Low Risk, High Frequency → Deterministic Checks**
   - Code formatting
   - Type checking
   - Schema validation

3. **Medium Risk → Spot Checks**
   - Sample validation
   - Key path testing
   - Output verification

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

## Example LLM-Aware Planning Scenarios

### Scenario 1: System Optimization (Minimizing LLM Calls)
```
Task: "Optimize database query performance"

LLM-Aware Plan:
1. Investigate current performance (→ Investigator)
   - Analyze slow queries
   - Identify patterns
   - OUTPUT: Performance report with specific queries
   
2. Design optimizations (→ Optimizer) 
   - Index recommendations
   - Query rewrites
   - Batch multiple optimization strategies
   - OUTPUT: Complete optimization plan
   
3. [DETERMINISTIC VALIDATION]
   - Syntax check all queries
   - Verify index names don't conflict
   - No LLM needed here
   
4. Implement changes (→ Process)
   - Create indexes
   - Update queries
   - Automated rollback on failure
   
5. Verify improvements (→ Process + Single LLM check)
   - Automated performance benchmarks
   - LLM only for interpreting unexpected results
```

### Scenario 2: Feature Implementation (Strategic Validation)
```
Task: "Add user authentication"

LLM-Aware Plan:
1. Design phase (→ Planning) [BUNDLED LLM TASK]
   - Define requirements
   - Create architecture
   - Design database schema
   - Plan API structure
   - OUTPUT: Complete design document
   
2. [VALIDATION CHECKPOINT - Second Opinion]
   - Architecture review by senior agent
   - Security considerations check
   - Only ONE additional LLM call
   
3. Implementation (→ Parallel) [PITFALL PREVENTION]
   - Database schema (→ Process with schema validation)
   - API endpoints (→ Developer agent with explicit examples)
   - UI components (→ Developer agent with design system constraints)
   - Each task includes specific pitfall warnings
   
4. [DETERMINISTIC VALIDATION]
   - Code compilation
   - Type checking  
   - Schema validation
   - No LLM calls needed
   
5. Integration (→ Sequential)
   - Connect components with clear interfaces
   - Add middleware with tested patterns
   - OUTPUT: Working integration
   
6. Testing (→ Hybrid approach)
   - Automated unit tests (deterministic)
   - Integration tests (deterministic)
   - Edge case identification (ONE LLM call)
   - User acceptance criteria check (ONE LLM review)
```

### Key Differences in LLM-Aware Planning:
1. **Bundled related tasks** to reduce LLM invocations
2. **Strategic validation points** not continuous checking
3. **Deterministic validation** wherever possible
4. **Clear outputs** to maintain context between steps
5. **Pitfall warnings** embedded in instructions

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

## Continuous Improvement for LLM Planning

The Planning Agent should track and optimize:

### LLM-Specific Metrics
1. **LLM Call Efficiency**
   - Average LLM calls per task
   - Validation call ratio
   - Unnecessary validation rate
   
2. **Failure Pattern Analysis**
   - Where do LLMs fail most?
   - Which validations catch most issues?
   - What context prevents failures?

3. **Plan Effectiveness**
   - Tasks completed without replanning
   - Recovery path usage
   - Context preservation success

### Improvement Strategies

1. **Pattern Documentation**
   - Successful task decompositions
   - Effective validation placements
   - Pitfall prevention techniques

2. **Template Development**
   - Common task patterns
   - Reusable validation strategies
   - Standard recovery procedures

3. **Validation Optimization**
   - Remove redundant checks
   - Convert LLM checks to deterministic
   - Adjust validation placement

### Learning from Failures

When plans fail, analyze:
1. Was it an LLM execution issue or planning issue?
2. Would different validation have caught it?
3. Could deterministic checks replace LLM validation?
4. Was context lost between steps?

### Best Practices Evolution

Continuously refine:
- Optimal task bundling sizes
- Most effective validation points
- Context preservation techniques
- Pitfall warning effectiveness

Regular reviews with Review Agent ensure planning strategies evolve to minimize LLM calls while maximizing success rates.