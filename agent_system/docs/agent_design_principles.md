# Agent Design Principles

## The Philosophy of Agent Design

Agents are not just instruction sets - they are cognitive configurations. Each agent is a specialized instance of the universal runtime, differentiated only by its instruction, context, tools, and constraints. The quality of an agent is determined by the precision and defensiveness of its configuration.

## Core Design Principles

### 1. Single Responsibility Principle
Every agent must have ONE clear, well-defined purpose. Complex tasks are achieved through agent collaboration, not complex agents.

**Good Examples:**
- `code_reviewer`: Reviews code for quality and standards
- `test_writer`: Writes tests for existing code
- `bug_finder`: Identifies potential bugs in code

**Bad Example:**
- `code_helper`: Reviews code, writes tests, fixes bugs, and refactors (too many responsibilities)

### 2. Defensive Programming First
Focus 80% on preventing failures, 20% on enabling capabilities. Define what the agent should NOT do before defining what it should do.

**Structure:**
1. Identity and constraints
2. Failure modes and edge cases  
3. Binary rules and policies
4. Only then: capabilities

### 3. Binary Rules Over Guidelines
Every behavioral rule must be binary (yes/no), not subjective.

**Transform:**
- "Be concise" → "Use maximum 3 sentences per response unless specified"
- "Be helpful" → "Always acknowledge requests. Never refuse without explanation"
- "Handle errors well" → "On error: 1) State what failed 2) Explain why 3) Suggest alternative"

### 4. Edge Case Exhaustion
For every capability, define behavior for:
- Standard case (happy path)
- Edge cases (boundary conditions)
- Error cases (failures)
- Ambiguous cases (unclear input)

### 5. Example-Driven Specification
Show, don't just tell. For every tool or complex behavior:
- Show CORRECT usage with expected output
- Show INCORRECT usage with explanation
- Show error handling

### 6. Cognitive Checkpoints
Build in reflection triggers:
- After tool usage: Verify output
- Before decisions: Check assumptions
- At completion: Validate success

### 7. Graceful Degradation
Every agent must know:
- When to ask for clarification
- When to delegate to another agent
- When to report limitations
- How to fail informatively

## Anti-Patterns to Avoid

### 1. The Swiss Army Knife
Creating agents that do too many things. Each tool should have one purpose.

### 2. The Optimist
Assuming happy paths without defining edge cases and failures.

### 3. The Mystic
Using vague, subjective language that's open to interpretation.

### 4. The Lone Wolf
Creating agents that don't delegate or ask for help when needed.

### 5. The Black Box
Not including reflection points or observable decision-making.

## Agent Instruction Template

```
You are the [Name] Agent responsible for [ONE specific thing].

IDENTITY AND CONSTANTS:
- Core capability: [What you do]
- Core constraint: [What you never do]
- Activation trigger: [When you're called]

DECISION ROUTING:
If [standard request]: [Standard procedure]
If [variant request]: [Variant handling]  
If [ambiguous request]: Ask "[Specific clarification]"
If [out-of-scope]: Delegate to [specific agent]

[FOR EACH TOOL:]
TOOL: [tool_name]
Purpose: [What it does]

CORRECT usage:
    tool_name(param1="value", param2=123)
    # Expected output: {structure}

INCORRECT usage:
    tool_name("value", 123)  # Missing parameter names
    # Error: Parameters must be named

BINARY RULES:
- Never [specific prohibition]
- Always [specific requirement]
- Maximum [specific limit]
- Minimum [specific threshold]

EDGE CASES:
If [edge case 1]: [Specific handling]
If [edge case 2]: [Specific handling]
If [error case]: [Error procedure]

REFLECTION CHECKPOINTS:
- After [action]: Verify [condition]
- Before [decision]: Check [assumption]
- On completion: Confirm [success criteria]

DELEGATION TRIGGERS:
- If [condition]: Delegate to [agent]
- If [condition]: Request help from [agent]

FAILURE HANDLING:
On [failure type]:
1. [Immediate action]
2. [User communication]
3. [Recovery or delegation]
```

## Testing Your Agent Design

Before deploying an agent, verify:

1. **Single Purpose Test**: Can you describe its job in one sentence?
2. **Edge Case Test**: Have you defined behavior for all edge cases?
3. **Binary Rule Test**: Are all rules yes/no, not maybe?
4. **Example Test**: Do you show both good and bad examples?
5. **Failure Test**: Does it know how to fail gracefully?
6. **Delegation Test**: Does it know when to ask for help?

## The Meta-Principle

The best agents are like good employees:
- They know their job and do it well
- They ask for clarification when confused
- They delegate when something's outside their expertise
- They can explain their reasoning
- They fail gracefully and learn from mistakes

Design agents that you would want to work with.