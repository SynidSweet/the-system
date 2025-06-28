#!/usr/bin/env python3
"""
Migrate existing agent entities to the agents table.
"""

import sqlite3
import json
from pathlib import Path

def migrate_agents():
    """Migrate agent entities to agents table."""
    db_path = Path(__file__).parent.parent / "data" / "agent_system.db"
    
    # Default agent configurations
    agent_configs = {
        "agent_selector": {
            "instruction": "Analyze the given task and select the most appropriate agent type to handle it. Consider task complexity, required skills, and available agent capabilities.",
            "context_documents": ["system_overview", "agent_registry"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "execute", "spawn_agents"],
            "constraints": []
        },
        "task_breakdown": {
            "instruction": "Break down the given task into sequential subtasks that can be handled by individual agents. Ensure each subtask is specific, actionable, and has clear success criteria.",
            "context_documents": ["breakdown_guidelines", "system_architecture"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "execute", "spawn_agents"],
            "constraints": []
        },
        "context_addition": {
            "instruction": "Determine what additional context documents are needed for the requesting agent to complete its task. Search existing documents and identify gaps.",
            "context_documents": ["available_context", "documentation_standards"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute"],
            "constraints": []
        },
        "tool_addition": {
            "instruction": "Find, create, or configure the MCP tools needed for the requesting agent's task. Search existing tools registry and external MCP servers.",
            "context_documents": ["tool_registry", "mcp_documentation"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute", "tool_management"],
            "constraints": []
        },
        "task_evaluator": {
            "instruction": "Evaluate the completed task result and determine if it meets the requirements. Assess quality, completeness, and correctness.",
            "context_documents": ["evaluation_criteria", "quality_standards"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "execute"],
            "constraints": []
        },
        "documentation_agent": {
            "instruction": "Document any system changes, new procedures, or important discoveries from the completed task. Update relevant context documents.",
            "context_documents": ["documentation_standards", "system_architecture"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute"],
            "constraints": []
        },
        "summary_agent": {
            "instruction": "Create a concise summary of task execution and results for the parent agent, filtering out redundant details while preserving essential information.",
            "context_documents": ["summarization_guidelines"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "execute"],
            "constraints": []
        },
        "supervisor": {
            "instruction": "Monitor system operations and ensure smooth functioning. Handle escalations and coordinate between agents.",
            "context_documents": ["system_overview", "agent_registry", "monitoring_guidelines"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute", "supervise"],
            "constraints": []
        },
        "review_agent": {
            "instruction": "Analyze flagged issues and determine system improvements needed. Implement fixes, optimizations, and enhancements based on identified patterns.",
            "context_documents": ["improvement_guide", "system_architecture"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute", "modify_system"],
            "constraints": []
        },
        "agent_creator": {
            "instruction": "Create new agent configurations based on system needs. Design agent instructions, assign appropriate tools and context.",
            "context_documents": ["agent_design_guide", "system_architecture"],
            "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
            "permissions": ["read", "write", "execute", "create_agents"],
            "constraints": []
        }
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all agent entities without corresponding agent records
        cursor.execute("""
            SELECT e.entity_id, e.name 
            FROM entities e 
            WHERE e.entity_type = 'agent' 
            AND NOT EXISTS (SELECT 1 FROM agents a WHERE a.id = e.entity_id)
        """)
        
        agents_to_migrate = cursor.fetchall()
        
        if not agents_to_migrate:
            print("No agents to migrate")
            return
        
        print(f"Migrating {len(agents_to_migrate)} agents...")
        
        for entity_id, name in agents_to_migrate:
            config = agent_configs.get(name, {
                "instruction": f"Agent {name} - instruction to be defined",
                "context_documents": [],
                "available_tools": ["break_down_task", "start_subtask", "request_context", "request_tools", "end_task", "flag_for_review"],
                "permissions": ["read", "execute"],
                "constraints": []
            })
            
            cursor.execute("""
                INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                name,
                config["instruction"],
                json.dumps(config["context_documents"]),
                json.dumps(config["available_tools"]),
                json.dumps(config["permissions"]),
                json.dumps(config["constraints"])
            ))
            
            print(f"✅ Migrated agent: {name} (ID: {entity_id})")
        
        conn.commit()
        print(f"\n✅ Successfully migrated {len(agents_to_migrate)} agents")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_agents()