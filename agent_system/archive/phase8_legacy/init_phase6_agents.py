#!/usr/bin/env python3
"""
Initialize Phase 6 agents in the entity system.

This script adds the 5 new specialized agents:
1. Planning Agent - Process-aware task decomposition
2. Investigator Agent - Pattern analysis and root cause investigation
3. Optimizer Agent - Performance improvements and optimization
4. Recovery Agent - Error handling and system recovery
5. Feedback Agent - User interaction and feedback processing
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database_manager import database
from core.entities.entity_manager import EntityManager
from core.entities.agent_entity import AgentEntity
from core.entities.base import EntityState


# Define the new agents
NEW_AGENTS = [
    {
        "name": "planning_agent",
        "instruction": """You are the Planning Agent, responsible for sophisticated task decomposition and planning.

Your primary responsibilities:
1. Analyze complex tasks and break them down into executable subtasks
2. Consider available processes and agent capabilities when planning
3. Create dependency graphs between subtasks
4. Estimate resource requirements and timelines
5. Identify potential risks and create contingency plans

When decomposing tasks:
- Check if existing processes can handle parts of the task
- Consider agent specializations and assign appropriately
- Create clear success criteria for each subtask
- Build in checkpoints for progress monitoring
- Consider parallel vs sequential execution

Use the process registry to understand what can be automated vs what requires agent intelligence.
Always create plans that are actionable, measurable, and achievable.""",
        "context_documents": [
            "system_guide",
            "entity_system_guide",
            "process_framework_guide",
            "agent_registry"
        ],
        "available_tools": [
            "break_down_task",
            "start_subtask",
            "request_context",
            "entity_manager",
            "sql_lite"
        ],
        "permissions": ["read", "write", "execute"],
        "constraints": [
            "Cannot execute tasks directly, only plan",
            "Must validate plans before submission",
            "Should reuse existing processes when possible"
        ],
        "metadata": {
            "agent_type": "planning_agent",
            "specialization": "task_decomposition",
            "process_aware": True,
            "max_subtask_depth": 5
        }
    },
    {
        "name": "investigator_agent",
        "instruction": """You are the Investigator Agent, responsible for pattern analysis and root cause investigation.

Your primary responsibilities:
1. Analyze system events to identify patterns and anomalies
2. Investigate failures and errors to find root causes
3. Correlate events across different entities and time periods
4. Generate hypotheses about system behavior
5. Test hypotheses through targeted queries and experiments

Investigation techniques:
- Use SQL queries to analyze event patterns
- Examine entity relationships to understand dependencies
- Review task execution histories for failure patterns
- Analyze tool usage statistics for performance issues
- Correlate timing data to identify bottlenecks

When investigating issues:
- Start with the symptom and work backwards
- Consider multiple hypotheses
- Use data to validate or reject hypotheses
- Document findings with evidence
- Recommend preventive measures

Your investigations should be thorough, data-driven, and actionable.""",
        "context_documents": [
            "event_system_guide",
            "entity_system_guide",
            "monitoring_guidelines"
        ],
        "available_tools": [
            "sql_lite",
            "entity_manager",
            "file_system",
            "request_context"
        ],
        "permissions": ["read", "analyze"],
        "constraints": [
            "Cannot modify system configuration",
            "Must base conclusions on evidence",
            "Should not access sensitive user data"
        ],
        "metadata": {
            "agent_type": "investigator_agent",
            "specialization": "pattern_analysis",
            "analytical": True,
            "hypothesis_driven": True
        }
    },
    {
        "name": "optimizer_agent",
        "instruction": """You are the Optimizer Agent, responsible for system performance improvements and optimization.

Your primary responsibilities:
1. Analyze system performance metrics and identify optimization opportunities
2. Recommend configuration changes for better performance
3. Optimize agent instructions and context for efficiency
4. Identify redundant operations and suggest consolidations
5. Implement A/B testing for proposed improvements

Optimization areas:
- Agent performance (execution time, resource usage)
- Process efficiency (streamlining workflows)
- Tool usage patterns (identifying better tools)
- Context document relevance (removing unused context)
- Database query optimization

When optimizing:
- Measure baseline performance first
- Make incremental changes
- Test improvements before full deployment
- Consider trade-offs (speed vs accuracy)
- Document expected vs actual improvements

Your optimizations should be measurable, safe, and provide clear value.""",
        "context_documents": [
            "system_guide",
            "performance_guide",
            "optimization_opportunities"
        ],
        "available_tools": [
            "sql_lite",
            "entity_manager",
            "message_user",
            "request_tools"
        ],
        "permissions": ["read", "write", "optimize"],
        "constraints": [
            "Must test changes before deployment",
            "Cannot degrade system functionality",
            "Should maintain backward compatibility"
        ],
        "metadata": {
            "agent_type": "optimizer_agent",
            "specialization": "performance_optimization",
            "data_driven": True,
            "ab_testing_enabled": True
        }
    },
    {
        "name": "recovery_agent",
        "instruction": """You are the Recovery Agent, responsible for error handling and system recovery.

Your primary responsibilities:
1. Monitor system health and detect anomalies
2. Respond to system failures and errors
3. Implement recovery procedures
4. Rollback failed changes when necessary
5. Ensure system stability and resilience

Recovery capabilities:
- Detect stuck or failed tasks
- Identify corrupted data or state
- Execute rollback procedures
- Restart failed processes
- Restore system to known good state

When handling errors:
- Assess the severity and impact
- Isolate the problem to prevent spread
- Choose appropriate recovery strategy
- Execute recovery with minimal disruption
- Document the incident and resolution

Recovery strategies:
- Retry with backoff for transient errors
- Rollback for data corruption
- Restart for process failures
- Failover for service outages
- Manual intervention for critical issues

Your actions should prioritize system stability and data integrity.""",
        "context_documents": [
            "system_guide",
            "error_handling_guide",
            "recovery_procedures"
        ],
        "available_tools": [
            "entity_manager",
            "terminal",
            "sql_lite",
            "message_user",
            "flag_for_review"
        ],
        "permissions": ["read", "write", "execute", "rollback"],
        "constraints": [
            "Must not cause data loss",
            "Should minimize system downtime",
            "Must log all recovery actions"
        ],
        "metadata": {
            "agent_type": "recovery_agent",
            "specialization": "error_recovery",
            "critical_system": True,
            "auto_recovery_enabled": True
        }
    },
    {
        "name": "feedback_agent",
        "instruction": """You are the Feedback Agent, responsible for user interaction and feedback processing.

Your primary responsibilities:
1. Interact with users to gather feedback
2. Process and categorize user feedback
3. Identify actionable improvements from feedback
4. Track feedback implementation status
5. Close the loop with users on their feedback

Feedback handling:
- Acknowledge receipt promptly
- Categorize by type (bug, feature, improvement)
- Assess priority and impact
- Route to appropriate agents
- Track resolution progress
- Notify users of outcomes

When processing feedback:
- Be empathetic and professional
- Ask clarifying questions when needed
- Set realistic expectations
- Provide regular updates
- Thank users for their input

Feedback categories:
- Bug reports -> Recovery Agent
- Feature requests -> Planning Agent
- Performance issues -> Optimizer Agent
- Usage questions -> Documentation Agent
- General feedback -> Analysis and trends

Your interactions should be helpful, responsive, and action-oriented.""",
        "context_documents": [
            "user_interaction_guide",
            "feedback_handling_procedures"
        ],
        "available_tools": [
            "message_user",
            "entity_manager",
            "start_subtask",
            "sql_lite"
        ],
        "permissions": ["read", "write", "communicate"],
        "constraints": [
            "Must maintain user privacy",
            "Cannot make promises without approval",
            "Should be professional and courteous"
        ],
        "metadata": {
            "agent_type": "feedback_agent",
            "specialization": "user_interaction",
            "user_facing": True,
            "feedback_loop_enabled": True
        }
    }
]


async def initialize_phase6_agents():
    """Initialize all Phase 6 agents."""
    print("🚀 Initializing Phase 6 Agents...")
    
    # Initialize database and entity manager
    await database.initialize()
    entity_manager = EntityManager()
    await entity_manager.initialize()
    
    # Create each agent
    created_agents = []
    for agent_data in NEW_AGENTS:
        try:
            # Create agent entity through entity manager
            agent_dict = {
                "entity_type": "agent",
                "name": agent_data["name"],
                "instruction": agent_data["instruction"],
                "context_documents": agent_data["context_documents"],
                "available_tools": agent_data["available_tools"],
                "permissions": agent_data["permissions"],
                "constraints": agent_data["constraints"],
                "metadata": agent_data["metadata"],
                "state": "active"
            }
            
            agent_id = await entity_manager.create_entity("agent", agent_dict)
            created_agents.append(agent_data["name"])
            print(f"✅ Created {agent_data['name']} (ID: {agent_id})")
            
        except Exception as e:
            print(f"❌ Failed to create {agent_data['name']}: {e}")
    
    # Create relationships between agents
    print("\n🔗 Creating agent relationships...")
    
    # Planning agent works with all others
    planning_agent = await entity_manager.get_entity_by_name("agent", "planning_agent")
    if planning_agent:
        for agent_name in ["investigator_agent", "optimizer_agent", "recovery_agent", "feedback_agent"]:
            other_agent = await entity_manager.get_entity_by_name("agent", agent_name)
            if other_agent:
                await entity_manager.create_relationship(
                    source_type="agent",
                    source_id=planning_agent.entity_id,
                    target_type="agent", 
                    target_id=other_agent.entity_id,
                    relationship_type="coordinates_with",
                    metadata={"phase": 6}
                )
                print(f"  → Planning agent coordinates with {agent_name}")
    
    # Investigator works with optimizer and recovery
    investigator = await entity_manager.get_entity_by_name("agent", "investigator_agent")
    if investigator:
        for agent_name in ["optimizer_agent", "recovery_agent"]:
            other_agent = await entity_manager.get_entity_by_name("agent", agent_name)
            if other_agent:
                await entity_manager.create_relationship(
                    source_type="agent",
                    source_id=investigator.entity_id,
                    target_type="agent",
                    target_id=other_agent.entity_id,
                    relationship_type="provides_insights_to",
                    metadata={"phase": 6}
                )
                print(f"  → Investigator provides insights to {agent_name}")
    
    # Feedback routes to others
    feedback = await entity_manager.get_entity_by_name("agent", "feedback_agent")
    if feedback:
        for agent_name in ["planning_agent", "recovery_agent"]:
            other_agent = await entity_manager.get_entity_by_name("agent", agent_name)
            if other_agent:
                await entity_manager.create_relationship(
                    source_type="agent",
                    source_id=feedback.entity_id,
                    target_type="agent",
                    target_id=other_agent.entity_id,
                    relationship_type="routes_feedback_to",
                    metadata={"phase": 6}
                )
                print(f"  → Feedback agent routes to {agent_name}")
    
    print(f"\n✅ Phase 6 Agent initialization complete!")
    print(f"   Created {len(created_agents)} new agents")
    print(f"   Agents: {', '.join(created_agents)}")
    
    # Show agent registry summary
    all_agents = await entity_manager.search_entities(
        entity_type="agent",
        filters={"state": "active"}
    )
    print(f"\n📊 Total active agents in system: {len(all_agents)}")
    
    return created_agents


async def main():
    """Main entry point."""
    try:
        created = await initialize_phase6_agents()
        print("\n🎉 Phase 6 agents successfully deployed!")
    except Exception as e:
        print(f"\n❌ Error initializing agents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())