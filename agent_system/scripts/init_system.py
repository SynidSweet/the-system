#!/usr/bin/env python3
"""
System initialization script for the self-improving agent system.

This script:
1. Initializes the database schema
2. Seeds core agents, tools, and context documents
3. Registers MCP tools
4. Performs system health checks
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from ..config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()
from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import register_core_tools
from tools.system_tools.mcp_integrations import register_system_tools


async def init_database() -> bool:
    """Initialize database connection and schema"""
    print("🔧 Initializing database...")
    
    try:
        await db_manager.connect()
        print("✅ Database connection established")
        print("✅ Database schema created")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def seed_core_agents() -> bool:
    """Seed the database with core agent configurations"""
    print("🤖 Seeding core agents...")
    
    from ..core.entities import AgentEntity
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
    
    core_agents = [
        {
            "name": "agent_selector",
            "instruction": "Analyze the given task and select the most appropriate agent type to handle it. If no suitable agent exists, recommend creating a new agent configuration. Consider task complexity, required skills, and available agent capabilities.",
            "context_documents": ["system_overview", "agent_registry"],
            "available_tools": ["database_query"],
            "permissions": AgentPermissions(
                web_search=True,
                database_write=False,
                spawn_agents=True
            )
        },
        {
            "name": "task_breakdown",
            "instruction": "Break down the given task into sequential subtasks that can be handled by individual agents. Ensure each subtask is specific, actionable, and has clear success criteria. Consider dependencies between subtasks.",
            "context_documents": ["breakdown_guidelines", "system_architecture"],
            "available_tools": [],
            "permissions": AgentPermissions(
                spawn_agents=True
            )
        },
        {
            "name": "context_addition",
            "instruction": "Determine what additional context documents are needed for the requesting agent to complete its task. Search existing documents and identify gaps. Create or update context documents as needed.",
            "context_documents": ["available_context", "documentation_standards"],
            "available_tools": ["database_query", "terminal_execution"],
            "permissions": AgentPermissions(
                web_search=True,
                database_write=True,
                file_system=True
            )
        },
        {
            "name": "tool_addition",
            "instruction": "Find, create, or configure the MCP tools needed for the requesting agent's task. Search existing tools registry, external MCP servers, and create custom tools when necessary.",
            "context_documents": ["tool_registry", "mcp_documentation"],
            "available_tools": ["database_query", "mcp_server_integration", "terminal_execution"],
            "permissions": AgentPermissions(
                web_search=True,
                database_write=True,
                file_system=True,
                shell_access=True
            )
        },
        {
            "name": "task_evaluator",
            "instruction": "Evaluate the completed task result and determine if it meets the requirements. Assess quality, completeness, and correctness. Provide feedback and suggest improvements if needed.",
            "context_documents": ["evaluation_criteria", "quality_standards"],
            "available_tools": ["database_query", "think_out_loud"],
            "permissions": AgentPermissions(
                database_write=True
            )
        },
        {
            "name": "documentation_agent",
            "instruction": "Document any system changes, new procedures, or important discoveries from the completed task. Update relevant context documents and maintain system knowledge base.",
            "context_documents": ["documentation_standards", "system_architecture"],
            "available_tools": ["database_query"],
            "permissions": AgentPermissions(
                database_write=True,
                file_system=True
            )
        },
        {
            "name": "summary_agent",
            "instruction": "Create a concise summary of task execution and results for the parent agent, filtering out redundant details while preserving essential information and insights.",
            "context_documents": ["summarization_guidelines"],
            "available_tools": ["database_query"],
            "permissions": AgentPermissions()
        },
        {
            "name": "review_agent",
            "instruction": "Analyze flagged issues and determine system improvements needed. Implement fixes, optimizations, and enhancements based on identified patterns and problems.",
            "context_documents": ["improvement_guide", "system_architecture"],
            "available_tools": ["database_query", "git_operations", "terminal_execution"],
            "permissions": AgentPermissions(
                web_search=True,
                database_write=True,
                file_system=True,
                shell_access=True,
                git_operations=True
            )
        }
    ]
    
    created_count = 0
    for agent_config in core_agents:
        try:
            # Check if agent already exists
            existing = await database.agents.get_by_name(agent_config["name"])
            if existing:
                print(f"  ⚠️  Agent '{agent_config['name']}' already exists, skipping")
                continue
            
            # Create agent
            agent = Agent(
                name=agent_config["name"],
                instruction=agent_config["instruction"],
                context_documents=agent_config["context_documents"],
                available_tools=agent_config["available_tools"],
                permissions=agent_config["permissions"]
            )
            
            agent_id = await database.agents.create(agent)
            print(f"  ✅ Created agent '{agent_config['name']}' (ID: {agent_id})")
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create agent '{agent_config['name']}': {e}")
    
    print(f"✅ Created {created_count} core agents")
    return True


async def seed_context_documents() -> bool:
    """Seed the database with initial context documents"""
    print("📚 Seeding context documents...")
    
    from ..core.entities import ContextEntity
    
    # Type alias for backward compatibility
    ContextDocument = ContextEntity
    
    context_docs = [
        {
            "name": "system_overview",
            "title": "Self-Improving Agent System Overview",
            "category": "system",
            "content": """# System Overview

This is a recursive agent system where a single universal agent design can solve complex problems by breaking them down into simpler tasks and spawning specialized instances of itself.

## Core Principles
1. Universal Agent Architecture - One design, infinite specializations
2. Recursive Task Decomposition - Complex problems → Simple tasks
3. Dynamic Capability Discovery - System expands its toolkit as needed
4. Self-Improving Architecture - Agents can modify the system
5. Isolated Task Trees - Parallel problem solving

## Key Components
- Universal Agent Runtime
- MCP Tool System
- Task Queue and Management
- Database-driven Configuration
- Self-modification Capabilities"""
        },
        {
            "name": "system_architecture",
            "title": "System Architecture and Components",
            "category": "system",
            "content": """# System Architecture

## Database Schema
- agents: Agent configurations and instructions
- tasks: Task management and trees
- messages: All agent communications
- tools: MCP tool registry
- context_documents: System knowledge base

## Core Components
- UniversalAgent: Executes any agent configuration
- TaskManager: Queue, concurrency, tree management
- DatabaseManager: All CRUD operations
- AIModelManager: Multi-provider AI integration
- MCPToolRegistry: Tool discovery and execution

## Agent Types
1. agent_selector - Routes tasks
2. task_breakdown - Decomposes complex tasks
3. context_addition - Manages knowledge
4. tool_addition - Expands capabilities
5. task_evaluator - Quality assurance
6. documentation_agent - Knowledge management
7. summary_agent - Information synthesis
8. supervisor - System monitoring
9. review_agent - System improvement"""
        },
        {
            "name": "agent_registry",
            "title": "Available Agent Types",
            "category": "reference",
            "content": """# Agent Registry

## Core Agents
- **agent_selector**: Task routing and agent selection
- **task_breakdown**: Complex task decomposition
- **context_addition**: Knowledge and context management
- **tool_addition**: Capability expansion
- **task_evaluator**: Quality assessment
- **documentation_agent**: System documentation
- **summary_agent**: Information synthesis
- **supervisor**: System monitoring
- **review_agent**: System improvement

## Usage Guidelines
- Use agent_selector for initial task routing
- Use task_breakdown for complex multi-step tasks
- Use specific agents for specialized capabilities
- All agents can spawn subtasks and request additional resources"""
        },
        {
            "name": "breakdown_guidelines",
            "title": "Task Breakdown Best Practices",
            "category": "process",
            "content": """# Task Breakdown Guidelines

## Principles
1. Each subtask should be independently executable
2. Clear success criteria for each subtask
3. Minimize dependencies between subtasks
4. Consider parallel execution opportunities

## Process
1. Analyze task complexity and scope
2. Identify major components or phases
3. Break into sequential steps
4. Define clear inputs/outputs for each step
5. Assign appropriate agent types

## Quality Checks
- Each subtask has specific, measurable goals
- Dependencies are clearly identified
- Resource requirements are reasonable
- Timeline estimates are realistic"""
        }
    ]
    
    created_count = 0
    for doc_config in context_docs:
        try:
            # Check if document already exists
            existing = await database.context_documents.get_by_name(doc_config["name"])
            if existing:
                print(f"  ⚠️  Document '{doc_config['name']}' already exists, skipping")
                continue
            
            # Create document
            doc = ContextDocument(
                name=doc_config["name"],
                title=doc_config["title"],
                category=doc_config["category"],
                content=doc_config["content"]
            )
            
            doc_id = await database.context_documents.create(doc)
            print(f"  ✅ Created document '{doc_config['name']}' (ID: {doc_id})")
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create document '{doc_config['name']}': {e}")
    
    print(f"✅ Created {created_count} context documents")
    return True


async def register_tools() -> bool:
    """Register all MCP tools with the tool registry"""
    print("🔧 Registering MCP tools...")
    
    try:
        # Register core tools
        core_tools = register_core_tools(tool_registry)
        print(f"  ✅ Registered {len(core_tools)} core tools")
        
        # Register system tools
        system_tools = register_system_tools(tool_registry)
        print(f"  ✅ Registered {len(system_tools)} system tools")
        
        # Print tool summary
        all_tools = tool_registry.list_tools()
        print(f"✅ Total tools registered: {sum(len(tools) for tools in all_tools.values())}")
        for category, tools in all_tools.items():
            print(f"  - {category}: {len(tools)} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool registration failed: {e}")
        return False


async def health_check() -> bool:
    """Perform system health checks"""
    print("🏥 Performing health checks...")
    
    checks_passed = 0
    total_checks = 4
    
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
    
    # Agent configurations
    try:
        selector = await database.agents.get_by_name("agent_selector")
        if selector:
            print(f"  ✅ Agents: Core agents configured")
            checks_passed += 1
        else:
            print(f"  ❌ Agents: Missing core agent configurations")
    except Exception as e:
        print(f"  ❌ Agent check failed: {e}")
    
    # Context documents
    try:
        overview = await database.context_documents.get_by_name("system_overview")
        if overview:
            print(f"  ✅ Context: Core documents available")
            checks_passed += 1
        else:
            print(f"  ❌ Context: Missing core documents")
    except Exception as e:
        print(f"  ❌ Context check failed: {e}")
    
    success_rate = checks_passed / total_checks
    if success_rate >= 0.75:
        print(f"✅ Health check passed ({checks_passed}/{total_checks})")
        return True
    else:
        print(f"❌ Health check failed ({checks_passed}/{total_checks})")
        return False


async def main() -> bool:
    """Main initialization function"""
    print("🚀 Initializing Self-Improving Agent System...")
    print("=" * 50)
    
    # Initialize database
    if not await init_database():
        print("💥 Database initialization failed, aborting")
        return False
    
    # Initialize database manager
    await database.initialize()
    
    # Seed data
    await seed_core_agents()
    await seed_context_documents()
    
    # Register tools
    if not await register_tools():
        print("💥 Tool registration failed, aborting")
        return False
    
    # Health check
    if not await health_check():
        print("💥 Health check failed, system may not function properly")
        return False
    
    print("=" * 50)
    print("🎉 System initialization completed successfully!")
    print("🤖 The self-improving agent system is ready to use.")
    print("")
    print("Next steps:")
    print("  1. Start the API server: python -m api.main")
    print("  2. Open web interface: http://localhost:8000")
    print("  3. Submit your first task!")
    
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