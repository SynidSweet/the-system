#!/usr/bin/env python3
"""
Minimal system initialization for the self-improving agent system.

This script implements the minimalist philosophy:
1. Initialize database schema
2. Seed ONLY the agent_selector (everything else built by agents)
3. Register core MCP tools
4. Perform basic health checks

The system will build all other capabilities through self-improvement.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from agent_system.config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()
from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import register_core_tools
from tools.system_tools.mcp_integrations import register_system_tools


async def init_database():
    """Initialize database connection and schema"""
    print("🔧 Initializing minimal database...")
    
    try:
        await db_manager.connect()
        print("✅ Database connection established")
        print("✅ Database schema created")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def seed_minimal_agents():
    """Seed ONLY the agent_selector - everything else built by agents"""
    print("🤖 Seeding minimal agent (agent_selector only)...")
    
    from agent_system.core.entities import AgentEntity
    from pydantic import BaseModel
    from typing import Optional
    
    # Temporary compatibility models
    class AgentPermissions(BaseModel):
        web_search: bool = False
        file_system: bool = False
        shell_access: bool = False
        git_operations: bool = False
        database_write: bool = False
        spawn_agents: bool = True
    
    class ModelConfig(BaseModel):
        provider: str = "google"
        model_name: str = "gemini-2.5-flash-preview-05-20"
        temperature: float = 0.1
        max_tokens: int = 4000
        api_key: Optional[str] = None
    
    # Type alias for backward compatibility
    Agent = AgentEntity
    
    # Only create the agent_selector - everything else will be built by agents
    agent_selector = Agent(
        name="agent_selector",
        instruction="""You are the agent_selector in a self-improving recursive agent system.

Your job is to analyze incoming tasks and determine the best approach:

1. **Simple tasks**: Handle directly if you can solve them in a few steps
2. **Complex tasks**: Break them down using break_down_task() or start_subtask() 
3. **Missing capabilities**: Use request_tools() to get agents to build what's needed
4. **Unknown domains**: Use request_context() to get domain knowledge

IMPORTANT: This system is designed to be self-improving. If you need capabilities that don't exist yet (like task_breakdown, context_addition, tool_addition agents), use request_tools() to ask for them to be built.

The system starts minimal and builds complexity through recursive self-improvement.

Always explain your reasoning using think_out_loud() and end with end_task().""",
        context_documents=["system_overview"],
        available_tools=["database_query", "think_out_loud"],
        permissions=AgentPermissions(
            web_search=True,
            database_write=False,  # Read-only initially
            spawn_agents=True
        ),
        constraints=AgentConstraints(
            max_execution_time=300,  # 5 minutes
            max_tool_calls=20,
            max_recursion_depth=10,
            memory_limit_mb=512
        )
    )
    
    try:
        # Check if agent already exists
        existing = await database.agents.get_by_name("agent_selector")
        if existing:
            print("  ⚠️  Agent 'agent_selector' already exists, skipping")
            return True
        
        agent_id = await database.agents.create(agent_selector)
        print(f"  ✅ Created agent_selector (ID: {agent_id})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create agent_selector: {e}")
        return False


async def seed_minimal_context():
    """Seed minimal context - just system overview"""
    print("📚 Seeding minimal context...")
    
    from agent_system.core.entities import ContextEntity
    
    # Type alias for backward compatibility
    ContextDocument = ContextEntity
    
    system_overview = ContextDocument(
        name="system_overview",
        title="System Overview - Minimal Core",
        category="system",
        content="""# Self-Improving Agent System - Core Overview

This is a recursive agent system that starts minimal and builds itself up.

## Core Principle: Bootstrap Self-Improvement

The system begins with only:
- Universal Agent Runtime (executes any task configuration)
- Core MCP Toolkit (6 tools for recursion and coordination)
- Database (agents, tasks, messages)
- Agent Selector (routes tasks and builds missing capabilities)

## Everything Else Gets Built By Agents

When agents need capabilities that don't exist, they use:
- `request_tools()` to get new MCP tools built
- `request_context()` to get knowledge documents created
- `start_subtask()` to spawn specialized agents
- `break_down_task()` to decompose complex problems

## Core MCP Tools Available
1. break_down_task() - Recursive problem decomposition
2. start_subtask() - Spawn specialized agents  
3. request_context() - Get knowledge and context
4. request_tools() - Get new capabilities built
5. end_task() - Complete tasks with results
6. flag_for_review() - Human oversight queue

## Current State: Minimal Bootstrap

The system currently has minimal capabilities. Submit tasks asking for:
- Task breakdown functionality
- Context management systems
- Tool discovery and creation
- Supervision and monitoring
- Git integration for self-modification
- Testing frameworks
- Advanced UI components

The agents will build these capabilities through recursive self-improvement."""
    )
    
    try:
        existing = await database.context_documents.get_by_name("system_overview")
        if existing:
            print("  ⚠️  Document 'system_overview' already exists, skipping")
            return True
        
        doc_id = await database.context_documents.create(system_overview)
        print(f"  ✅ Created system_overview (ID: {doc_id})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create system_overview: {e}")
        return False


async def register_tools():
    """Register core MCP tools only"""
    print("🔧 Registering core MCP tools...")
    
    try:
        # Register core tools only
        core_tools = register_core_tools(tool_registry)
        print(f"  ✅ Registered {len(core_tools)} core tools")
        
        # Register minimal system tools  
        system_tools = register_system_tools(tool_registry)
        print(f"  ✅ Registered {len(system_tools)} system tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool registration failed: {e}")
        return False


async def health_check():
    """Minimal health check"""
    print("🏥 Performing minimal health check...")
    
    checks_passed = 0
    total_checks = 3
    
    # Database connectivity
    try:
        agents = await database.agents.get_all_active()
        print(f"  ✅ Database: {len(agents)} active agents found")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
    
    # Tool registry
    try:
        tools = tool_registry.list_tools()
        tool_count = sum(len(tools) for tools in tools.values())
        print(f"  ✅ Tools: {tool_count} tools registered")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ Tool registry check failed: {e}")
    
    # Agent selector
    try:
        selector = await database.agents.get_by_name("agent_selector")
        if selector:
            print(f"  ✅ Core: agent_selector ready")
            checks_passed += 1
        else:
            print(f"  ❌ Core: agent_selector missing")
    except Exception as e:
        print(f"  ❌ Agent check failed: {e}")
    
    if checks_passed >= 2:
        print(f"✅ Minimal core ready ({checks_passed}/{total_checks})")
        return True
    else:
        print(f"❌ Core initialization failed ({checks_passed}/{total_checks})")
        return False


async def main():
    """Main initialization function"""
    print("🚀 Initializing Minimal Self-Improving Agent Core...")
    print("=" * 60)
    print("Philosophy: Build less, enable more - let agents build the rest")
    print("=" * 60)
    
    # Initialize database
    if not await init_database():
        print("💥 Database initialization failed, aborting")
        return False
    
    # Initialize database manager
    await database.initialize()
    
    # Seed minimal data (only agent_selector)
    if not await seed_minimal_agents():
        print("💥 Agent seeding failed, aborting") 
        return False
        
    if not await seed_minimal_context():
        print("💥 Context seeding failed, aborting")
        return False
    
    # Register tools
    if not await register_tools():
        print("💥 Tool registration failed, aborting")
        return False
    
    # Health check
    if not await health_check():
        print("💥 Health check failed")
        return False
    
    print("=" * 60)
    print("🎉 Minimal core initialized successfully!")
    print("🤖 The self-improving agent system is ready to bootstrap itself.")
    print("")
    print("Next steps:")
    print("  1. Start the API server: python -m api.main")
    print("  2. Open web interface: http://localhost:8000/app")
    print("  3. Submit tasks asking agents to build missing functionality:")
    print("     - 'Build a task breakdown system for complex problems'")
    print("     - 'Create context management and knowledge tools'") 
    print("     - 'Implement supervision and monitoring agents'")
    print("     - 'Add git integration for self-modification'")
    print("")
    print("The agents will build everything else through recursive self-improvement!")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Initialization failed: {e}")
        sys.exit(1)