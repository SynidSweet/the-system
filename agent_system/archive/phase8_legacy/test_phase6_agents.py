#!/usr/bin/env python3
"""
Test script to verify Phase 6 agent configurations.

This validates the agent definitions without requiring database access.
"""

import json
from typing import Dict, List, Any


# Agent definitions from migration
PHASE6_AGENTS = [
    {
        "name": "planning_agent",
        "specialization": "task_decomposition",
        "tools": ["break_down_task", "start_subtask", "request_context", "entity_manager", "sql_lite"],
        "permissions": ["read", "write", "execute"],
        "coordinates_with": ["investigator_agent", "optimizer_agent", "recovery_agent", "feedback_agent"]
    },
    {
        "name": "investigator_agent", 
        "specialization": "pattern_analysis",
        "tools": ["sql_lite", "entity_manager", "file_system", "request_context"],
        "permissions": ["read", "analyze"],
        "provides_insights_to": ["optimizer_agent", "recovery_agent"]
    },
    {
        "name": "optimizer_agent",
        "specialization": "performance_optimization",
        "tools": ["sql_lite", "entity_manager", "message_user", "request_tools"],
        "permissions": ["read", "write", "optimize"],
        "receives_insights_from": ["investigator_agent"]
    },
    {
        "name": "recovery_agent",
        "specialization": "error_recovery",
        "tools": ["entity_manager", "terminal", "sql_lite", "message_user", "flag_for_review"],
        "permissions": ["read", "write", "execute", "rollback"],
        "receives_insights_from": ["investigator_agent"],
        "receives_feedback_from": ["feedback_agent"]
    },
    {
        "name": "feedback_agent",
        "specialization": "user_interaction",
        "tools": ["message_user", "entity_manager", "start_subtask", "sql_lite"],
        "permissions": ["read", "write", "communicate"],
        "routes_feedback_to": ["planning_agent", "recovery_agent"]
    }
]


def validate_agent_relationships():
    """Validate that all agent relationships are properly defined."""
    print("🔍 Validating Agent Relationships...")
    
    issues = []
    agents_map = {agent["name"]: agent for agent in PHASE6_AGENTS}
    
    for agent in PHASE6_AGENTS:
        name = agent["name"]
        
        # Check outgoing relationships
        for rel_type in ["coordinates_with", "provides_insights_to", "routes_feedback_to"]:
            if rel_type in agent:
                for target in agent[rel_type]:
                    if target not in agents_map:
                        issues.append(f"{name} references unknown agent: {target}")
                    else:
                        # Verify reciprocal relationship
                        target_agent = agents_map[target]
                        expected_rel = {
                            "coordinates_with": "coordinates_with",
                            "provides_insights_to": "receives_insights_from",
                            "routes_feedback_to": "receives_feedback_from"
                        }[rel_type]
                        
                        if expected_rel in target_agent:
                            if name not in target_agent.get(expected_rel, []):
                                print(f"  ⚠️  Missing reciprocal: {target} should have {expected_rel} {name}")
    
    if issues:
        print(f"❌ Found {len(issues)} relationship issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ All relationships are valid!")
    
    return len(issues) == 0


def validate_tool_availability():
    """Check that all referenced tools exist in the system."""
    print("\n🔍 Validating Tool References...")
    
    # Known system tools
    known_tools = {
        # Core MCP tools
        "break_down_task", "start_subtask", "request_context", "request_tools",
        "end_task", "flag_for_review",
        # MCP servers
        "entity_manager", "message_user", "file_system", "sql_lite", 
        "terminal", "github"
    }
    
    unknown_tools = set()
    
    for agent in PHASE6_AGENTS:
        for tool in agent["tools"]:
            if tool not in known_tools:
                unknown_tools.add(tool)
    
    if unknown_tools:
        print(f"❌ Unknown tools referenced: {unknown_tools}")
        return False
    else:
        print("✅ All tool references are valid!")
        return True


def validate_permissions():
    """Validate permission configurations."""
    print("\n🔍 Validating Permissions...")
    
    valid_permissions = {"read", "write", "execute", "analyze", "optimize", "rollback", "communicate"}
    issues = []
    
    for agent in PHASE6_AGENTS:
        for perm in agent["permissions"]:
            if perm not in valid_permissions:
                issues.append(f"{agent['name']} has invalid permission: {perm}")
    
    if issues:
        print(f"❌ Permission issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All permissions are valid!")
        return True


def show_agent_summary():
    """Display a summary of Phase 6 agents."""
    print("\n📊 Phase 6 Agent Summary:")
    print("=" * 60)
    
    for agent in PHASE6_AGENTS:
        print(f"\n🤖 {agent['name'].replace('_', ' ').title()}")
        print(f"   Specialization: {agent['specialization']}")
        print(f"   Tools: {', '.join(agent['tools'])}")
        print(f"   Permissions: {', '.join(agent['permissions'])}")
        
        # Show relationships
        rels = []
        if "coordinates_with" in agent:
            rels.append(f"coordinates with {len(agent['coordinates_with'])} agents")
        if "provides_insights_to" in agent:
            rels.append(f"provides insights to {len(agent['provides_insights_to'])} agents")
        if "routes_feedback_to" in agent:
            rels.append(f"routes feedback to {len(agent['routes_feedback_to'])} agents")
        
        if rels:
            print(f"   Relationships: {', '.join(rels)}")


def generate_integration_diagram():
    """Generate a simple text diagram of agent interactions."""
    print("\n🔗 Agent Integration Diagram:")
    print("=" * 60)
    print("""
    ┌─────────────────┐
    │ Feedback Agent  │──────┐
    └────────┬────────┘      │
             │               │ Routes feedback
             │               ▼
    ┌────────▼────────┐  ┌─────────────────┐
    │ Planning Agent  │◄─┤ Recovery Agent  │
    └────────┬────────┘  └────────▲────────┘
             │ Coordinates        │
             │ with all          │ Receives
    ┌────────▼────────┐          │ insights
    │  Investigator   │──────────┤
    │     Agent       │          │
    └────────┬────────┘          │
             │ Provides insights │
             ▼                   │
    ┌─────────────────┐         │
    │ Optimizer Agent │─────────┘
    └─────────────────┘
    
    Legend:
    ─────► Direction of information flow
    ◄────► Bidirectional coordination
    """)


def main():
    """Run all validation tests."""
    print("🧪 Testing Phase 6 Agent Configurations")
    print("=" * 60)
    
    # Run validations
    rel_valid = validate_agent_relationships()
    tool_valid = validate_tool_availability()
    perm_valid = validate_permissions()
    
    # Show summary
    show_agent_summary()
    
    # Show integration diagram
    generate_integration_diagram()
    
    # Final result
    print("\n" + "=" * 60)
    if rel_valid and tool_valid and perm_valid:
        print("✅ All Phase 6 agent configurations are valid!")
        print("\nNext steps:")
        print("1. Execute migration 004_add_phase6_agents.sql")
        print("2. Execute migration 005_add_phase6_context_documents.sql")
        print("3. Test agent interactions with sample tasks")
    else:
        print("❌ Some validation issues found. Please review above.")
    
    return rel_valid and tool_valid and perm_valid


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)