#!/usr/bin/env python3
"""
Initialize the process_discovery agent and neutral_task_process in the entity-based system.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Change to the agent_system directory
agent_system_dir = Path(__file__).parent.parent
os.chdir(agent_system_dir)
sys.path.insert(0, str(agent_system_dir))

# Import components
from config.database import db_manager


async def create_process_discovery_agent():
    """Create the process_discovery agent entity."""
    print("Creating process_discovery agent...")
    
    # Read the instruction from the guide
    guide_path = Path("context_documents/process_discovery_guide.md")
    if guide_path.exists():
        with open(guide_path, 'r') as f:
            guide_content = f.read()
        
        # Extract the instruction portion
        instruction = """You are the Process Discovery Agent, responsible for analyzing task domains and establishing comprehensive systematic process frameworks before any task execution begins.

Your primary responsibility is to ensure that EVERY task domain has a complete systematic framework established before any execution begins. You transform undefined problems into systematic domains with rules, regulations, and comprehensive context that enables isolated task success.

When analyzing any task, ask:
- "What systematic framework does this domain require?" (NOT "How do I solve this task?")
- "What processes need to exist for isolated subtasks to succeed?" (NOT "What's the quickest solution?")
- "Is the structural foundation complete?" (NOT "Can I work around missing structure?")

Core responsibilities:
1. Domain Analysis - Classify incoming tasks and determine required systematic structure
2. Process Gap Identification - Compare requirements against existing frameworks
3. Framework Establishment - Create comprehensive process frameworks for gaps
4. Isolation Validation - Ensure subtasks can succeed independently
5. Framework Documentation - Document all processes comprehensively"""
    else:
        instruction = "Process Discovery Agent - Analyzes domains and establishes systematic frameworks"
    
    try:
        # First, get the next entity_id for agents
        max_id_result = await db_manager.execute_query("""
            SELECT MAX(entity_id) as max_id FROM entities WHERE entity_type = 'agent'
        """)
        next_id = (max_id_result[0]['max_id'] or 0) + 1 if max_id_result else 1
        
        # Insert into entities table
        await db_manager.execute_command("""
            INSERT INTO entities (entity_type, entity_id, name, version, status, metadata, created_at, updated_at)
            VALUES ('agent', ?, 'process_discovery', '1.0.0', 'active', ?, datetime('now'), datetime('now'))
        """, (
            next_id,
            json.dumps({
                "description": "Primary agent for process-first framework establishment",
                "priority": "critical",
                "capabilities": [
                    "domain_analysis",
                    "framework_establishment", 
                    "process_gap_identification",
                    "isolation_validation"
                ],
                "instruction": instruction
            })
        ))
        
        print(f"✅ Created process_discovery agent (entity_id: {next_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error creating process_discovery agent: {e}")
        return False


async def create_neutral_task_process():
    """Create/register the neutral_task_process."""
    print("\nRegistering neutral_task_process...")
    
    try:
        # Check if it already exists
        existing = await db_manager.execute_query("""
            SELECT * FROM processes WHERE name = 'neutral_task_process'
        """)
        
        if existing:
            print("✅ neutral_task_process already exists")
            return True
        
        # Create the process
        await db_manager.execute_command("""
            INSERT INTO processes (name, description, process_type, status, metadata, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, datetime('now'), datetime('now'))
        """, (
            'neutral_task_process',
            'Process-first task process ensuring systematic framework establishment before execution',
            'task_processing',
            json.dumps({
                "phases": [
                    "process_discovery",
                    "framework_validation",
                    "agent_selection",
                    "context_assignment",
                    "tool_assignment",
                    "isolation_validation"
                ],
                "priority": "primary",
                "applies_to": "all_tasks"
            })
        ))
        
        print("✅ Created neutral_task_process")
        return True
        
    except Exception as e:
        print(f"❌ Error creating neutral_task_process: {e}")
        return False


async def create_process_discovery_process():
    """Create the process_discovery_process."""
    print("\nRegistering process_discovery_process...")
    
    try:
        # Check if it already exists
        existing = await db_manager.execute_query("""
            SELECT * FROM processes WHERE name = 'process_discovery_process'
        """)
        
        if existing:
            print("✅ process_discovery_process already exists")
            return True
        
        # Create the process
        await db_manager.execute_command("""
            INSERT INTO processes (name, description, process_type, status, metadata, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, datetime('now'), datetime('now'))
        """, (
            'process_discovery_process',
            'Analyzes task domains and establishes comprehensive systematic frameworks',
            'framework_establishment',
            json.dumps({
                "phases": [
                    "domain_analysis",
                    "process_gap_identification",
                    "framework_establishment",
                    "framework_validation",
                    "task_preparation"
                ],
                "execution_order": "sequential",
                "required_agent": "process_discovery"
            })
        ))
        
        print("✅ Created process_discovery_process")
        return True
        
    except Exception as e:
        print(f"❌ Error creating process_discovery_process: {e}")
        return False


async def verify_setup():
    """Verify the setup was successful."""
    print("\nVerifying setup...")
    
    # Check agent
    agents = await db_manager.execute_query("""
        SELECT * FROM entities WHERE entity_type = 'agent' AND name = 'process_discovery'
    """)
    
    if agents:
        print("✅ process_discovery agent found")
    else:
        print("❌ process_discovery agent not found")
    
    # Check processes
    processes = await db_manager.execute_query("""
        SELECT name FROM processes WHERE name IN ('neutral_task_process', 'process_discovery_process')
    """)
    
    if processes:
        print(f"✅ Found {len(processes)} processes:")
        for p in processes:
            print(f"   - {p['name']}")
    else:
        print("❌ No processes found")


async def main():
    """Initialize process_discovery components."""
    print("🚀 Initializing Process Discovery Components")
    print("=" * 50)
    
    try:
        # Connect to database
        await db_manager.connect()
        
        # Create components
        agent_success = await create_process_discovery_agent()
        neutral_process_success = await create_neutral_task_process()
        discovery_process_success = await create_process_discovery_process()
        
        # Verify
        await verify_setup()
        
        # Summary
        print("\n" + "=" * 50)
        if agent_success and neutral_process_success and discovery_process_success:
            print("✅ Process discovery components initialized successfully!")
            print("\nThe system now has:")
            print("- process_discovery agent for framework establishment")
            print("- neutral_task_process for process-first task handling")
            print("- process_discovery_process for systematic analysis")
        else:
            print("❌ Some components failed to initialize")
            
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())