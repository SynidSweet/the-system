#!/usr/bin/env python3
"""
Simple test to verify basic system functionality without running the full API.
"""

import asyncio
import sys
import os
from pathlib import Path

# Change to the agent_system directory
agent_system_dir = Path(__file__).parent.parent
os.chdir(agent_system_dir)
sys.path.insert(0, str(agent_system_dir))

# Import minimal components
from config.database import db_manager


async def test_database_connection():
    """Test that we can connect to the database."""
    print("Testing database connection...")
    try:
        await db_manager.connect()
        print("✅ Database connection successful")
        
        # Check if tables exist
        tables = await db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['name']}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_agent_exists():
    """Test that process_discovery agent exists."""
    print("\nTesting agent existence...")
    try:
        agents = await db_manager.execute_query(
            "SELECT * FROM agents WHERE name = 'process_discovery'"
        )
        if agents:
            print("✅ process_discovery agent found")
            return True
        else:
            print("❌ process_discovery agent not found")
            return False
    except Exception as e:
        print(f"❌ Error checking agents: {e}")
        return False


async def test_minimal_task_creation():
    """Test creating a task directly in the database."""
    print("\nTesting task creation...")
    try:
        import uuid
        from datetime import datetime
        
        # Get the next task ID
        result = await db_manager.execute_query(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM tasks"
        )
        task_id = result[0][0] if result else 1
        tree_id = task_id  # For root tasks, tree_id = task_id
        
        # Create a simple task
        await db_manager.execute_command("""
            INSERT INTO tasks (id, tree_id, parent_task_id, agent_id, instruction, 
                             status, result, metadata)
            VALUES (?, ?, NULL, NULL, ?, 'created', '{}', '{}')
        """, (
            task_id,
            tree_id,
            "TEST TASK: Simple arithmetic test"
        ))
        
        # Verify it was created
        tasks = await db_manager.execute_query(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        )
        
        if tasks:
            print(f"✅ Task created successfully: {task_id}")
            return True
        else:
            print("❌ Task creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False


async def main():
    """Run minimal tests."""
    print("🧪 Minimal System Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Database connection
    if await test_database_connection():
        tests_passed += 1
    
    # Test 2: Agent exists
    if await test_agent_exists():
        tests_passed += 1
    
    # Test 3: Task creation
    if await test_minimal_task_creation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✅ Basic system components are working!")
    else:
        print("❌ Some basic tests failed. The system needs initialization.")
    
    # Close database
    await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())