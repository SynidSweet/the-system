# Gemini 2.5 Model Series Configuration

## Overview

The system now uses Google's Gemini 2.5 model series, which includes three models optimized for different use cases:

### Available Models

#### 1. Gemini 2.5 Flash-Lite (Default)
- **Use Case**: Fast, cost-efficient tasks
- **Best For**: 
  - Classification and validation
  - Simple summarization
  - Quick routing decisions
  - High-volume operations
- **Context Window**: 1 million tokens
- **Relative Cost**: 1x (baseline)
- **Relative Speed**: 10x (fastest)
- **Default For**: agent_selector, task_evaluator, summary_agent

#### 2. Gemini 2.5 Flash
- **Use Case**: Balanced performance for general tasks
- **Best For**:
  - Code generation
  - Task planning and decomposition
  - General agent operations
  - Multi-step reasoning
- **Context Window**: 1 million tokens
- **Relative Cost**: 3x
- **Relative Speed**: 5x
- **Default For**: task_breakdown, planning_agent, most general agents

#### 3. Gemini 2.5 Pro
- **Use Case**: Complex reasoning and critical tasks
- **Best For**:
  - Architectural decisions
  - Deep code analysis
  - Critical validations
  - Complex investigations
- **Context Window**: 2 million tokens
- **Relative Cost**: 10x
- **Relative Speed**: 2x
- **Default For**: review_agent, investigator_agent

## Configuration

### System Default
The system default is set to **Gemini 2.5 Flash-Lite** for maximum speed and cost efficiency during testing and development.

### Agent-Specific Models
Each agent has a preferred model based on its typical workload:

```python
AGENT_MODEL_PREFERENCES = {
    "agent_selector": "gemini-2.5-flash-lite",     # Fast routing
    "task_breakdown": "gemini-2.5-flash",          # Balanced planning
    "context_addition": "gemini-2.5-flash",        # General purpose
    "tool_addition": "gemini-2.5-flash",           # General purpose
    "task_evaluator": "gemini-2.5-flash-lite",     # Quick validation
    "documentation_agent": "gemini-2.5-flash",     # Quality docs
    "summary_agent": "gemini-2.5-flash-lite",      # Fast summaries
    "review_agent": "gemini-2.5-pro",              # Critical review
    "planning_agent": "gemini-2.5-flash",          # Strategic planning
    "investigator_agent": "gemini-2.5-pro",        # Deep analysis
    "optimizer_agent": "gemini-2.5-flash",         # Optimization
    "feedback_agent": "gemini-2.5-flash",          # User interaction
    "recovery_agent": "gemini-2.5-flash"           # Error recovery
}
```

### Dynamic Model Selection
The system can dynamically select models based on:
1. Task complexity
2. Required accuracy
3. Time constraints
4. Cost optimization goals

## Migration Notes

The system has been updated from Gemini 2.5 Flash Preview to the complete Gemini 2.5 series:
- Previous: `gemini-2.5-flash-preview-05-20`
- Current: `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`

## Best Practices

### When to Use Each Model

1. **Use Flash-Lite for**:
   - High-frequency, low-complexity tasks
   - Initial routing and classification
   - Quick validations that don't require deep reasoning
   - Cost-sensitive operations

2. **Use Flash for**:
   - Most general agent tasks
   - Code generation and modification
   - Task planning and decomposition
   - Standard analysis and reasoning

3. **Use Pro for**:
   - Critical architectural decisions
   - Complex problem solving
   - Deep code analysis and optimization
   - Tasks where accuracy is paramount

### Cost Optimization

- The system defaults to Flash-Lite to minimize costs during development
- Agents automatically use their preferred models
- Consider batch processing with Flash-Lite for bulk operations
- Reserve Pro model for truly complex tasks

### Performance Tips

- Flash-Lite is 5x faster than Flash and 10x faster than Pro
- Use streaming for Pro model to improve perceived responsiveness
- Consider breaking complex Pro tasks into Flash subtasks when possible
- Monitor token usage as Pro supports 2x the context of other models