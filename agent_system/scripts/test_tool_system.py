#!/usr/bin/env python3
"""
Test script for Phase 5: Optional Tooling System

This script tests:
1. Tool permission system
2. MCP server registration and operation
3. Dynamic tool assignment
4. Tool usage tracking
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from core.database_manager import database
from core.entities.entity_manager import EntityManager
from core.events.event_manager import EventManager
from core.permissions.manager import DatabasePermissionManager, ToolAssignment
from tools.mcp_servers.startup import initialize_tool_system, get_tool_system_manager


async def test_permission_system():
    """Test the permission management system."""
    print("\n🔍 Testing Permission System...")
    
    # Initialize permission manager
    perm_manager = DatabasePermissionManager(database)
    
    # Test 1: Get base permissions for agent
    print("\n1. Testing base permissions...")
    permissions = await perm_manager.get_agent_permissions("agent_selector")
    print(f"   Base tools for agent_selector: {permissions.tools}")
    print(f"   Entity access: {permissions.entity_access}")
    
    # Test 2: Assign tool to task
    print("\n2. Testing tool assignment...")
    tool_assignment = ToolAssignment(
        tool_name="sql_lite",
        assignment_reason="Test assignment for database analysis",
        duration_hours=24,
        specific_permissions={"allowed_queries": ["get_recent_events"]}
    )
    
    success = await perm_manager.assign_tool_to_task(
        task_id=1,
        tool_assignment=tool_assignment,
        assigned_by=1
    )
    print(f"   Tool assignment success: {success}")
    
    # Test 3: Get permissions with task-specific tools
    print("\n3. Testing task-specific permissions...")
    task_permissions = await perm_manager.get_agent_permissions("agent_selector", task_id=1)
    print(f"   Tools with task assignment: {task_permissions.tools}")
    print(f"   Tool-specific permissions: {task_permissions.tool_permissions}")
    
    # Test 4: Check specific permissions
    print("\n4. Testing permission checks...")
    can_read_agent = await perm_manager.check_permission("agent_selector", 1, "read", "agent")
    can_write_agent = await perm_manager.check_permission("agent_selector", 1, "write", "agent")
    print(f"   Can read agent: {can_read_agent}")
    print(f"   Can write agent: {can_write_agent}")
    
    print("\n✅ Permission system tests complete!")


async def test_mcp_servers():
    """Test MCP server functionality."""
    print("\n🔍 Testing MCP Servers...")
    
    # Initialize entity manager
    entity_manager = EntityManager()
    await entity_manager.initialize()
    
    # Initialize tool system
    tool_system = await initialize_tool_system(
        db_manager=database,
        entity_manager=entity_manager,
        config={
            "allowed_file_paths": ["/code/personal/the-system"],
            "github": {},
            "user_interface": {}
        }
    )
    
    # Test 1: Check registered servers
    print("\n1. Testing server registration...")
    status = tool_system.get_system_status()
    print(f"   Registered servers: {list(status['mcp_servers'].keys())}")
    print(f"   Total servers: {status['total_servers']}")
    
    # Test 2: Entity Manager MCP operations
    print("\n2. Testing Entity Manager MCP...")
    try:
        # Get agent through MCP
        result = await tool_system.call_tool(
            tool_name="entity_manager",
            operation="list_agents",
            parameters={},
            agent_type="agent_selector",
            task_id=1
        )
        print(f"   Listed {len(result)} agents through MCP")
    except Exception as e:
        print(f"   Entity Manager test failed: {e}")
    
    # Test 3: Message User MCP operations
    print("\n3. Testing Message User MCP...")
    try:
        result = await tool_system.call_tool(
            tool_name="message_user",
            operation="send_message",
            parameters={
                "message": "Test message from tool system",
                "message_type": "info"
            },
            agent_type="agent_selector",
            task_id=1
        )
        print(f"   Message sent successfully: {result}")
    except Exception as e:
        print(f"   Message User test failed: {e}")
    
    print("\n✅ MCP server tests complete!")


async def test_tool_usage_tracking():
    """Test tool usage tracking."""
    print("\n🔍 Testing Tool Usage Tracking...")
    
    perm_manager = DatabasePermissionManager(database)
    
    # Log some tool usage
    print("\n1. Logging tool usage...")
    await perm_manager.log_tool_usage(
        task_id=1,
        agent_type="agent_selector",
        tool_name="entity_manager",
        operation="list_agents",
        success=True,
        execution_time_ms=50,
        result_summary="Listed 10 agents"
    )
    
    await perm_manager.log_tool_usage(
        task_id=1,
        agent_type="agent_selector",
        tool_name="message_user",
        operation="send_message",
        success=True,
        execution_time_ms=25,
        result_summary="Message sent"
    )
    
    # Get usage stats
    print("\n2. Getting usage statistics...")
    stats = await perm_manager.get_tool_usage_stats(days=1)
    for stat in stats:
        print(f"   {stat['tool_name']} by {stat['agent_type']}: "
              f"{stat['usage_count']} uses, "
              f"{stat['success_rate']:.2%} success rate, "
              f"{stat['avg_execution_time']:.1f}ms avg time")
    
    print("\n✅ Tool usage tracking tests complete!")


async def test_complete_flow():
    """Test complete tool request and assignment flow."""
    print("\n🔍 Testing Complete Tool Flow...")
    
    # This would test:
    # 1. Agent requests tool via need_more_tools
    # 2. Request validation process
    # 3. Tool addition agent assigns tool
    # 4. Agent uses newly assigned tool
    
    print("   (Complete flow test requires full system running)")
    print("\n✅ Complete flow test placeholder complete!")


async def main():
    """Run all tests."""
    print("🧪 Phase 5: Optional Tooling System Tests")
    print("=" * 60)
    
    try:
        # Initialize database
        await db_manager.connect()
        await database.initialize()
        
        # Run tests
        await test_permission_system()
        await test_mcp_servers()
        await test_tool_usage_tracking()
        await test_complete_flow()
        
        print("\n" + "=" * 60)
        print("✅ All Phase 5 tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())