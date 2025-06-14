# Thinking and Transparency Update for Agent Guides

## Overview

All agent context guides should be updated to emphasize the use of `think_out_loud()` tool for transparency and debugging. This update ensures consistency with the recent system-wide emphasis on transparent reasoning.

## Update Required for All Agent Guides

Each agent guide should include a section on thinking transparency. Here's the template to add:

### Thinking and Transparency (Add to each guide)

```markdown
## Thinking Process and Transparency

Use `think_out_loud()` liberally throughout your task execution to create transparency:

### When to Think Out Loud
- **Initial Assessment**: Log your first impressions and understanding of the task
- **Decision Points**: Document reasoning behind major decisions
- **Uncertainty**: Express doubts, alternatives considered, and why you chose a path
- **Observations**: Note patterns, insights, or unexpected findings
- **Planning**: Share your approach before executing
- **Reflection**: Log what worked, what didn't, and lessons learned

### Example Usage
```python
think_out_loud("Analyzing task complexity - appears to require coordination between 3 domains: UI, database, and external API integration. This suggests task_breakdown would be appropriate.", thought_type="planning")

think_out_loud("Noticed the existing agent 'data_processor' has similar capabilities but lacks API integration tools. Considering whether to enhance existing agent or create new specialized one.", thought_type="decision", confidence=0.7)
```

This transparency serves multiple purposes:
1. **Debugging**: Helps identify where reasoning went wrong
2. **Learning**: Captures insights for system improvement
3. **Collaboration**: Helps other agents understand your approach
4. **Trust**: Builds confidence through explainable decisions
```

## Agents Requiring Updates

All agent guides in `/docs/agent_contexts/` need this section added:
- agent_selector_guide.md
- task_breakdown_guide.md
- context_addition_guide.md
- tool_addition_guide.md
- task_evaluator_guide.md
- documentation_agent_guide.md
- summary_agent_guide.md
- supervisor_guide.md
- review_agent_guide.md

## Implementation Note

The universal agent instruction and individual agent instructions in the database have already been updated. These documentation files should be updated to match.