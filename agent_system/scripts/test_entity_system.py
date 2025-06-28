#!/usr/bin/env python3
"""
Test script that works with the entity-based architecture.
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


async def test_database_structure():
    """Verify the entity-based database structure."""
    print("Testing entity-based database structure...")
    try:
        await db_manager.connect()
        
        # Check entity tables
        required_tables = ['entities', 'processes', 'process_instances']
        found_tables = []
        
        tables = await db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        
        table_names = [t['name'] for t in tables]
        
        for required in required_tables:
            if required in table_names:
                found_tables.append(required)
                print(f"✅ Found table: {required}")
            else:
                print(f"❌ Missing table: {required}")
        
        return len(found_tables) == len(required_tables)
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


async def test_process_discovery_entity():
    """Check if process_discovery exists as an entity."""
    print("\nChecking for process_discovery entity...")
    try:
        # Look for process_discovery in entities table
        entities = await db_manager.execute_query("""
            SELECT * FROM entities 
            WHERE entity_type = 'agent' AND name = 'process_discovery'
        """)
        
        if entities:
            entity = entities[0]
            print(f"✅ Found process_discovery agent entity:")
            print(f"   - Entity ID: {entity['entity_id']}")
            print(f"   - Status: {entity['status']}")
            print(f"   - Version: {entity['version']}")
            return True
        else:
            print("❌ process_discovery agent entity not found")
            
            # Check all agents
            all_agents = await db_manager.execute_query("""
                SELECT name FROM entities WHERE entity_type = 'agent'
            """)
            if all_agents:
                print("   Available agents:")
                for agent in all_agents:
                    print(f"   - {agent['name']}")
            else:
                print("   No agent entities found in the system")
            
            return False
    except Exception as e:
        print(f"❌ Error checking entities: {e}")
        return False


async def test_process_creation():
    """Test creating a process instance."""
    print("\nTesting process instance creation...")
    try:
        import uuid
        
        # Check if neutral_task_process exists
        processes = await db_manager.execute_query("""
            SELECT * FROM processes WHERE name = 'neutral_task_process'
        """)
        
        if not processes:
            print("❌ neutral_task_process not found")
            return False
        
        process = processes[0]
        print(f"✅ Found neutral_task_process (ID: {process['id']})")
        
        # Create a process instance
        # First get a task ID
        result = await db_manager.execute_query(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM tasks"
        )
        task_id = result[0][0] if result else 1
        
        input_data = {
            "instruction": "TEST: Calculate 42 + 58",
            "context": {},
            "test": True
        }
        
        await db_manager.execute_command("""
            INSERT INTO process_instances 
            (process_id, task_id, parameters, state, status)
            VALUES (?, ?, ?, 'initialized', 'pending')
        """, (
            process['id'],
            task_id,
            json.dumps(input_data)
        ))
        
        # Verify creation
        instances = await db_manager.execute_query(
            "SELECT * FROM process_instances WHERE task_id = ?", (task_id,)
        )
        
        if instances:
            print(f"✅ Process instance created for task: {task_id}")
            return True
        else:
            print("❌ Failed to create process instance")
            return False
            
    except Exception as e:
        print(f"❌ Error creating process instance: {e}")
        return False


async def main():
    """Run entity-based system tests."""
    print("🧪 Entity-Based System Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Database structure
    if await test_database_structure():
        tests_passed += 1
    
    # Test 2: Process discovery entity
    if await test_process_discovery_entity():
        tests_passed += 1
    
    # Test 3: Process creation
    if await test_process_creation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✅ Entity-based system is properly configured!")
        print("\nThe system is ready for initialization.")
    else:
        print("❌ Entity system needs initialization.")
        print("\nRun the initialization script to set up agents and processes.")
    
    # Close database
    await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())