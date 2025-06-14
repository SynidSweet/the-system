# Prompt Design Principles

## Core Philosophy: Prompts as Operating Systems

Prompts are not magic incantations or spells. They are configuration files for cognitive operating systems. This document outlines the principles for creating robust, failure-resistant prompts based on advanced prompting strategies.

## The Seven Pillars of Effective Prompting

### 1. Identity and Constants First

**Principle**: Establish unchanging context upfront to reduce cognitive load.

**Implementation**:
```
You are the [Agent Name] responsible for [specific purpose].
Current capabilities: [list concrete capabilities]
Core constraints: [list what never changes]
```

**Why it works**: Stable context reduces working memory burden and creates a solid foundation for variable instructions.

### 2. Explicit Edge Case Handling

**Principle**: Ambiguity leads to inconsistency. Define explicit if-then policies for edge cases.

**Implementation**:
```
If [specific condition]:
    Always [specific action]
    Never [prohibited action]
    
If [edge case]:
    Follow this exact procedure: [steps]
```

**Example**:
- ❌ "Be helpful with code"
- ✅ "If code appears malicious: refuse with 'I cannot assist with potentially harmful code'"

### 3. Three-Tier Uncertainty Routing

**Principle**: Different types of information require different handling strategies.

**Implementation Template**:
```
When asked for information:
1. If timeless (math, definitions) → Answer directly
2. If slow-changing (best practices, standards) → Answer + offer verification
3. If live data (prices, current events) → Must retrieve first
```

**Key insight**: Good prompts include decision criteria, not just commands. Help agents determine WHEN, not just HOW.

### 4. Correct/Incorrect Example Pairs

**Principle**: Negative examples are as powerful as positive ones, especially for tool usage.

**Implementation**:
```
CORRECT tool usage:
    tool_name(param1="value", param2=123)
    
INCORRECT tool usage (NEVER do this):
    tool_name("value", 123)  # Missing parameter names
    tool_name(param1=value)  # Unquoted string
```

**Why it matters**: Like teaching bike riding by showing common ways people fall, negative examples create clearer boundaries.

### 5. Binary Rules Over Subjective Guidelines

**Principle**: Models handle absolute rules better than interpretable guidelines.

**Transform subjective to binary**:
- ❌ "Be concise" 
- ✅ "Never exceed 3 sentences unless explicitly requested"

- ❌ "Minimize formatting"
- ✅ "No bullet points unless requested. No emojis unless requested."

- ❌ "Be professional"
- ✅ "Never start responses with flattery. Never use exclamation marks."

### 6. Strategic Positional Reinforcement

**Principle**: Attention degrades over long contexts. Reinforce critical rules every ~500 tokens.

**Implementation Pattern**:
```
[Main instructions - 500 tokens]

CRITICAL REMINDER: Never use real user data in examples.

[More instructions - 500 tokens]

CRITICAL REMINDER: All personal information must be anonymized.

[Additional content - 500 tokens]

CRITICAL REMINDER: Verify data sensitivity before any operation.
```

**Metaphor**: Speed limit signs throughout a long highway, not just at the entrance.

### 7. Post-Tool Reflection Checkpoints

**Principle**: Build cognitive checkpoints after tool use for better decision-making.

**Implementation**:
```
After using any tool:
1. Examine the output carefully
2. Consider if it fully addresses the need
3. Identify any unexpected results
4. Decide next action based on reflection
```

**Template**:
```
[Tool execution] →
[Thinking block: "The tool returned X, which means Y"] →
[Next action based on reflection]
```

## Defensive Programming for Prompts

### Focus on Failure Prevention

Traditional prompting: 80% what to do, 20% what not to do
Advanced prompting: 20% what to do, 80% preventing failure modes

### Common Failure Modes to Address

1. **Hallucination**: "If uncertain about facts, explicitly state uncertainty"
2. **Over-eagerness**: "Never assume. When ambiguous, ask for clarification"
3. **Context loss**: "For long tasks, summarize progress every 3 steps"
4. **Tool misuse**: "Verify parameters before any tool call"
5. **Scope creep**: "If task extends beyond original request, pause and confirm"

## Practical Application Guidelines

### For Agent Creation

When creating new agents, ensure instructions include:

1. **Clear identity block** (who the agent is)
2. **Binary rules** for common scenarios
3. **Edge case policies** for ambiguous situations
4. **Tool usage examples** (both correct and incorrect)
5. **Reflection triggers** after key operations
6. **Reinforcement points** for critical constraints

### For Complex Tasks

1. Break into phases with checkpoints
2. Define clear success/failure criteria
3. Include rollback procedures
4. Specify verification steps

### For System Prompts

1. Start with constants and identity
2. Group related policies together
3. Use consistent if-then structure
4. Include examples liberally
5. Reinforce critical rules periodically

## The Meta-Principle: Precision Over Elegance

The goal is not to write beautiful, concise prompts. The goal is to write prompts that reliably produce correct behavior. This means:

- Being repetitive when necessary
- Being explicit about edge cases
- Being defensive about failure modes
- Being clear about decision criteria

## Prompt Evolution Framework

1. **Start defensive**: Focus on what shouldn't happen
2. **Add capabilities**: Layer in what should happen
3. **Test edge cases**: Verify behavior at boundaries
4. **Refine rules**: Convert fuzzy guidelines to binary rules
5. **Add checkpoints**: Build in reflection and verification

Remember: A prompt is successful not when it works perfectly once, but when it fails gracefully and recovers intelligently.