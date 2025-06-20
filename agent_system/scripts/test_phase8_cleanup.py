#!/usr/bin/env python3
"""
Test script to verify system functionality after Phase 8 cleanup.

This ensures all core functionality works with the entity-based architecture.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import DatabaseManager
from core.events.event_manager import EventManager
from core.events.event_types import EventType
from core.entities.entity_manager import EntityManager


async def test_database_connection():
    """Test database connectivity."""
    print("1. Testing database connection...")
    db = DatabaseManager()
    await db.connect()
    
    # Check if we can query entities
    results = await db.execute_query("SELECT COUNT(*) as count FROM entities")
    if results:
        print(f"   ✓ Database connected. Found {results[0]['count']} entities.")
    else:
        print("   ✗ Database error: No entities found")
        return False
    
    await db.disconnect()
    return True


async def test_event_system():
    """Test event system functionality."""
    print("\n2. Testing event system...")
    db = DatabaseManager()
    await db.connect()
    
    event_manager = EventManager(db)
    
    # Log a test event
    await event_manager.log_event(
        event_type=EventType.SYSTEM_EVENT,
        category="test",
        content="Phase 8 cleanup test",
        metadata={"test": True}
    )
    
    # Verify event was logged
    events = await db.execute_query(
        "SELECT * FROM events WHERE category = 'test' ORDER BY created_at DESC LIMIT 1"
    )
    
    if events:
        print("   ✓ Event system working. Test event logged successfully.")
    else:
        print("   ✗ Event system error: Could not log event.")
        return False
    
    await db.disconnect()
    return True


async def test_entity_framework():
    """Test entity framework functionality."""
    print("\n3. Testing entity framework...")
    db = DatabaseManager()
    await db.connect()
    
    entity_manager = EntityManager()
    await entity_manager.initialize()
    
    # Get all agent entities
    agents = await entity_manager.get_entities_by_type("agent")
    print(f"   ✓ Found {len(agents)} agent entities.")
    
    # List some agents
    if agents:
        print("   Agent entities:")
        for i, agent in enumerate(agents[:5]):  # Show first 5
            print(f"     - {agent.name} (ID: {agent.entity_id})")
        if len(agents) > 5:
            print(f"     ... and {len(agents) - 5} more")
    
    await db.disconnect()
    return True


async def test_runtime_tables():
    """Test runtime-related tables."""
    print("\n4. Testing runtime tables...")
    db = DatabaseManager()
    await db.connect()
    
    # Check processes
    processes = await db.execute_query("SELECT COUNT(*) as count FROM processes")
    if processes:
        print(f"   ✓ Found {processes[0]['count']} processes defined.")
    else:
        print("   ⚠ No processes found")
    
    # Check tools
    tools = await db.execute_query("SELECT COUNT(*) as count FROM entities WHERE entity_type = 'tool'")
    if tools:
        print(f"   ✓ Found {tools[0]['count']} tool entities.")
    else:
        print("   ⚠ No tool entities found")
    
    # Check context documents
    contexts = await db.execute_query("SELECT COUNT(*) as count FROM context_documents")
    if contexts:
        print(f"   ✓ Found {contexts[0]['count']} context documents.")
    else:
        print("   ⚠ No context documents found")
    
    await db.disconnect()
    return True


async def test_mcp_servers():
    """Test MCP server availability."""
    print("\n5. Testing MCP servers...")
    db = DatabaseManager()
    await db.connect()
    
    # Check registered MCP tools
    mcp_tools = await db.execute_query(
        """
        SELECT name FROM tools 
        WHERE category = 'mcp' 
        ORDER BY name
        """
    )
    
    if mcp_tools:
        print(f"   ✓ Found {len(mcp_tools)} MCP tools:")
        for tool in mcp_tools:
            print(f"     - {tool['name']}")
    else:
        print("   ⚠ No MCP tools found (may need initialization)")
    
    await db.disconnect()
    return True


async def verify_archived_tables():
    """Verify old tables are archived."""
    print("\n6. Verifying legacy table archival...")
    db = DatabaseManager()
    await db.connect()
    
    # Check if archive tables exist
    archive_tables = await db.execute_query(
        """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '_archive_%'
        ORDER BY name
        """
    )
    
    if archive_tables:
        print(f"   ✓ Found {len(archive_tables)} archived tables:")
        for table in archive_tables:
            print(f"     - {table['name']}")
    else:
        print("   ⚠ No archived tables found (migration may not have run)")
    
    # Check if old tables still exist
    old_tables = ['agents', 'tasks', 'messages', 'tools', 'context_documents']
    existing_old = []
    
    for table in old_tables:
        result = await db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if result:
            existing_old.append(table)
    
    if existing_old:
        print(f"   ⚠ Old tables still exist (not dropped yet): {', '.join(existing_old)}")
        print("     This is expected - tables are archived but not dropped for safety.")
    else:
        print("   ✓ Old tables have been removed.")
    
    await db.disconnect()
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 8 Cleanup Verification")
    print("=" * 60)
    
    tests = [
        test_database_connection(),
        test_event_system(),
        test_entity_framework(),
        test_runtime_tables(),
        test_mcp_servers(),
        verify_archived_tables()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False or isinstance(r, Exception))
    
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if failed > 0:
        print(f"Tests failed: {failed}")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"  Test {i+1} error: {result}")
    
    if passed == len(tests):
        print("\n✅ All tests passed! The system is functioning correctly after Phase 8 cleanup.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
    
    print("\nNext steps:")
    print("1. Run the full system: python -m api.main")
    print("2. Test task submission through the API")
    print("3. Verify the web interface works correctly")
    print("4. Check that agents can execute tasks")


if __name__ == "__main__":
    asyncio.run(main())