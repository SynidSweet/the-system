#!/usr/bin/env python3
"""
Add the neutral_task_process to the processes table.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Change to the agent_system directory
agent_system_dir = Path(__file__).parent.parent
os.chdir(agent_system_dir)
sys.path.insert(0, str(agent_system_dir))

from config.database import db_manager


async def create_neutral_task_process():
    """Create the neutral_task_process in the processes table."""
    print("Creating neutral_task_process...")
    
    try:
        # Check if it already exists
        existing = await db_manager.execute_query("""
            SELECT * FROM processes WHERE name = 'neutral_task_process'
        """)
        
        if existing:
            print("✅ neutral_task_process already exists")
            return True
        
        # Define the process template
        template = [
            {
                "step_id": "process_discovery",
                "name": "Process Discovery and Framework Establishment",
                "description": "Check for systematic framework and establish if missing",
                "required": True,
                "condition": "no_systematic_framework_id"
            },
            {
                "step_id": "framework_validation",
                "name": "Framework Validation",
                "description": "Validate framework completeness for isolated task success",
                "required": True
            },
            {
                "step_id": "agent_selection",
                "name": "Framework-Driven Agent Selection",
                "description": "Select optimal agent within systematic framework",
                "required": True,
                "condition": "no_assigned_agent"
            },
            {
                "step_id": "context_assignment",
                "name": "Framework-Driven Context Assignment",
                "description": "Assign framework-appropriate context documents",
                "required": True
            },
            {
                "step_id": "tool_assignment",
                "name": "Framework-Appropriate Tool Assignment",
                "description": "Assign tools that comply with framework boundaries",
                "required": True
            },
            {
                "step_id": "isolation_validation",
                "name": "Isolated Task Success Validation",
                "description": "Verify task can succeed independently with assigned resources",
                "required": True
            }
        ]
        
        parameters_schema = {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The task ID to process"
                }
            },
            "required": ["task_id"]
        }
        
        success_criteria = [
            "Task has systematic framework established",
            "Framework is validated as complete",
            "Agent is assigned within framework constraints",
            "Context and tools are framework-appropriate",
            "Task can succeed in isolation"
        ]
        
        # Insert the process
        await db_manager.execute_command("""
            INSERT INTO processes (
                name, description, category, template, parameters_schema, 
                success_criteria, version, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'neutral_task_process',
            'Process-first task process ensuring systematic framework establishment before execution',
            'task_processing',
            json.dumps(template),
            json.dumps(parameters_schema),
            json.dumps(success_criteria),
            '1.0.0',
            'active'
        ))
        
        print("✅ Created neutral_task_process")
        return True
        
    except Exception as e:
        print(f"❌ Error creating neutral_task_process: {e}")
        return False


async def create_process_discovery_process():
    """Create the process_discovery_process in the processes table."""
    print("\nCreating process_discovery_process...")
    
    try:
        # Check if it already exists
        existing = await db_manager.execute_query("""
            SELECT * FROM processes WHERE name = 'process_discovery_process'
        """)
        
        if existing:
            print("✅ process_discovery_process already exists")
            return True
        
        # Define the process template
        template = [
            {
                "step_id": "domain_analysis",
                "name": "Comprehensive Domain Analysis",
                "description": "Analyze task domain and classify systematic requirements",
                "required": True
            },
            {
                "step_id": "gap_identification",
                "name": "Process Gap Identification",
                "description": "Compare requirements against existing frameworks",
                "required": True
            },
            {
                "step_id": "framework_establishment",
                "name": "Systematic Framework Establishment",
                "description": "Create missing process frameworks before execution",
                "required": True,
                "condition": "gaps_identified"
            },
            {
                "step_id": "framework_validation",
                "name": "Framework Completeness Validation",
                "description": "Validate framework enables isolated task success",
                "required": True
            },
            {
                "step_id": "task_preparation",
                "name": "Systematic Task Preparation",
                "description": "Prepare task with complete framework information",
                "required": True
            }
        ]
        
        parameters_schema = {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "The task ID to analyze"
                },
                "instruction": {
                    "type": "string",
                    "description": "The task instruction to analyze"
                }
            },
            "required": ["task_id", "instruction"]
        }
        
        success_criteria = [
            "Domain type identified and classified",
            "All process gaps identified",
            "Missing frameworks established",
            "Framework validated as complete",
            "Task prepared with systematic framework"
        ]
        
        # Insert the process
        await db_manager.execute_command("""
            INSERT INTO processes (
                name, description, category, template, parameters_schema, 
                success_criteria, version, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'process_discovery_process',
            'Analyzes task domains and establishes comprehensive systematic frameworks',
            'framework_establishment',
            json.dumps(template),
            json.dumps(parameters_schema),
            json.dumps(success_criteria),
            '1.0.0',
            'active'
        ))
        
        print("✅ Created process_discovery_process")
        return True
        
    except Exception as e:
        print(f"❌ Error creating process_discovery_process: {e}")
        return False


async def verify_setup():
    """Verify everything is set up correctly."""
    print("\nVerifying setup...")
    
    # Check agent
    agents = await db_manager.execute_query("""
        SELECT e.entity_id, e.name, e.description 
        FROM entities e 
        JOIN agents a ON e.entity_id = a.id 
        WHERE e.name = 'process_discovery'
    """)
    
    if agents:
        print(f"✅ process_discovery agent found (ID: {agents[0]['entity_id']})")
    else:
        print("❌ process_discovery agent not found")
    
    # Check processes
    processes = await db_manager.execute_query("""
        SELECT id, name, category, status 
        FROM processes 
        WHERE name IN ('neutral_task_process', 'process_discovery_process')
        ORDER BY name
    """)
    
    if processes:
        print(f"✅ Found {len(processes)} processes:")
        for p in processes:
            print(f"   - {p['name']} (category: {p['category']}, status: {p['status']})")
    else:
        print("❌ No processes found")


async def main():
    """Set up process discovery components."""
    print("🚀 Setting up Process Discovery Components")
    print("=" * 50)
    
    try:
        # Connect to database
        await db_manager.connect()
        
        # Create processes
        neutral_success = await create_neutral_task_process()
        discovery_success = await create_process_discovery_process()
        
        # Verify
        await verify_setup()
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ Process discovery setup complete!")
        print("\nThe system now has:")
        print("- process_discovery agent for framework establishment")
        print("- neutral_task_process for process-first task handling")
        print("- process_discovery_process for systematic analysis")
        print("\nYou can now run the lateral test to verify the system works!")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())