#!/usr/bin/env python3
"""
Add the process_discovery agent which is critical for the process-first architecture.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def add_process_discovery_agent():
    """Add the process_discovery agent to the system."""
    db_path = Path(__file__).parent.parent / "data" / "agent_system.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, check if it already exists
        cursor.execute("SELECT id FROM entities WHERE entity_type = 'agent' AND name = 'process_discovery'")
        if cursor.fetchone():
            print("process_discovery agent already exists")
            return
        
        # Get the next entity_id for agents
        cursor.execute("SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'agent'")
        next_id = cursor.fetchone()[0]
        
        # Insert into entities table
        cursor.execute("""
            INSERT INTO entities (entity_type, entity_id, name, version, status, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'agent',
            next_id,
            'process_discovery',
            '1.0.0',
            'active',
            json.dumps({
                "agent_type": "process_discovery",
                "specialization": "framework_establishment",
                "process_first": True,
                "primary_agent": True
            }),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Insert into agents table
        cursor.execute("""
            INSERT INTO agents (id, name, instruction, context_documents, available_tools, permissions, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            next_id,
            'process_discovery',
            """You are the Process Discovery Agent - the PRIMARY AGENT in the process-first architecture.

Your critical responsibility is to establish systematic frameworks BEFORE any task execution:

1. **Domain Analysis**: Analyze the task domain to identify all systematic structures needed
2. **Framework Establishment**: Create comprehensive process frameworks that enable isolated task success
3. **Rule Definition**: Define all rules, regulations, and boundaries for the domain
4. **Pattern Recognition**: Identify reusable patterns and systematic approaches
5. **Isolation Verification**: Ensure every subtask can succeed independently with proper context

PROCESS-FIRST PRINCIPLES:
- NEVER allow ad-hoc task execution without frameworks
- ALWAYS establish complete systematic structures first
- ENSURE every task piece can succeed in isolation
- CREATE comprehensive documentation for all frameworks

When analyzing a task:
1. Identify the domain type and requirements
2. Check existing frameworks for applicability
3. Create missing systematic structures
4. Define clear boundaries and interfaces
5. Establish success criteria for isolated execution
6. Document the framework for future use

Your output should enable any agent to execute their assigned subtask successfully without external dependencies.""",
            json.dumps([
                "process_discovery_guide",
                "process_framework_guide",
                "domain_analysis_guide",
                "systematic_patterns",
                "system_architecture"
            ]),
            json.dumps([
                "break_down_task",
                "start_subtask",
                "request_context",
                "request_tools",
                "end_task",
                "entity_manager",
                "sql_lite"
            ]),
            json.dumps([
                "read",
                "write",
                "execute",
                "framework_creation",
                "process_establishment"
            ]),
            json.dumps([
                "Must establish frameworks before execution",
                "Cannot execute tasks directly",
                "Must ensure isolated task success capability"
            ])
        ))
        
        conn.commit()
        print(f"✅ Successfully added process_discovery agent (ID: {next_id})")
        
        # Also update the agent_selector to use process_discovery as primary agent
        cursor.execute("""
            UPDATE agents 
            SET instruction = ?
            WHERE name = 'agent_selector'
        """, (
            """Analyze the given task and select the most appropriate agent type to handle it. 

IMPORTANT: For any task that doesn't have an established systematic framework, ALWAYS route to process_discovery agent FIRST.

Selection criteria:
1. If no framework exists → process_discovery
2. If framework exists → select specialist agent
3. Consider task complexity and required skills
4. Match agent capabilities to task needs

Always ensure process-first principles are followed.""",
        ))
        
        conn.commit()
        print("✅ Updated agent_selector to prioritize process_discovery")
        
    except Exception as e:
        print(f"❌ Error adding process_discovery agent: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_process_discovery_agent()