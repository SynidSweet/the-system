"""
Base seeder classes for system data initialization.

This module provides base classes and utilities for seeding agents, tools,
and documents into the system database.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Any, Optional
from pathlib import Path

from .config_loader import SeedConfiguration, AgentConfig, ToolConfig, DocumentConfig


class BaseSeeder(ABC):
    """Abstract base class for all seeders"""
    
    def __init__(self, database_manager):
        self.database = database_manager
    
    @abstractmethod
    async def seed(self, config: SeedConfiguration) -> bool:
        """Seed data from configuration. Returns True if successful."""
        pass
    
    def log_progress(self, message: str, success: bool = True):
        """Log seeding progress with consistent formatting"""
        icon = "✅" if success else "❌"
        print(f"  {icon} {message}")


class AgentSeeder(BaseSeeder):
    """Seeder for agent configurations"""
    
    async def seed(self, config: SeedConfiguration) -> bool:
        """Seed all agents from configuration"""
        print("🤖 Seeding agents from configuration...")
        
        try:
            from agent_system.core.entities import AgentEntity
            
            agents_added = 0
            agents_skipped = 0
            
            for agent_config in config.agents:
                try:
                    # Check if agent already exists
                    existing = await self.database.agents.get_by_name(agent_config.name)
                    if existing:
                        self.log_progress(f"Agent '{agent_config.name}' already exists, skipping")
                        agents_skipped += 1
                        continue
                    
                    # Create agent entity
                    agent = AgentEntity(
                        name=agent_config.name,
                        instruction=agent_config.instruction,
                        context_documents=agent_config.context_documents,
                        available_tools=agent_config.available_tools,
                        permissions=agent_config.permissions.dict()
                    )
                    
                    agent_id = await self.database.agents.create(agent)
                    self.log_progress(f"Added agent '{agent_config.name}' (ID: {agent_id})")
                    agents_added += 1
                    
                except Exception as e:
                    self.log_progress(f"Failed to add agent '{agent_config.name}': {e}", success=False)
                    return False
            
            print(f"🤖 Agent seeding complete: {agents_added} added, {agents_skipped} skipped")
            return True
            
        except Exception as e:
            print(f"❌ Agent seeding failed: {e}")
            return False


class ToolSeeder(BaseSeeder):
    """Seeder for tool configurations"""
    
    async def seed(self, config: SeedConfiguration) -> bool:
        """Seed all tools from configuration"""
        print("🔧 Seeding tools from configuration...")
        
        try:
            from agent_system.core.entities import ToolEntity
            from tools.base_tool import tool_registry
            from tools.core_mcp.core_tools import register_core_tools
            from tools.system_tools.mcp_integrations import register_system_tools
            from tools.system_tools.internal_tools import register_internal_tools
            
            # Register tools with the registry first
            try:
                core_tools = register_core_tools(tool_registry)
                self.log_progress(f"Registered {len(core_tools)} core tools")
                
                system_tools = register_system_tools(tool_registry)
                self.log_progress(f"Registered {len(system_tools)} system tools")
                
                internal_tools = register_internal_tools(tool_registry)
                self.log_progress(f"Registered {len(internal_tools)} internal tools")
                
            except Exception as e:
                self.log_progress(f"Tool registration failed: {e}", success=False)
                return False
            
            # Add tools to database
            tools_added = 0
            tools_skipped = 0
            
            for tool_config in config.tools:
                try:
                    # Check if tool already exists
                    existing = await self.database.tools.get_by_name(tool_config.name)
                    if existing:
                        self.log_progress(f"Tool '{tool_config.name}' already exists, skipping")
                        tools_skipped += 1
                        continue
                    
                    # Create tool entity
                    tool = ToolEntity(
                        name=tool_config.name,
                        description=tool_config.description,
                        category=tool_config.category,
                        implementation=tool_config.implementation.dict(),
                        parameters=tool_config.parameters,
                        permissions=tool_config.permissions
                    )
                    
                    tool_id = await self.database.tools.create(tool)
                    self.log_progress(f"Added tool '{tool_config.name}' (ID: {tool_id})")
                    tools_added += 1
                    
                except Exception as e:
                    self.log_progress(f"Failed to add tool '{tool_config.name}': {e}", success=False)
                    return False
            
            print(f"🔧 Tool seeding complete: {tools_added} added, {tools_skipped} skipped")
            return True
            
        except Exception as e:
            print(f"❌ Tool seeding failed: {e}")
            return False


class DocumentSeeder(BaseSeeder):
    """Seeder for context document configurations"""
    
    async def seed(self, config: SeedConfiguration) -> bool:
        """Seed all documents from configuration"""
        print("📚 Seeding documents from configuration...")
        
        try:
            from agent_system.core.entities import ContextEntity
            
            docs_added = 0
            docs_skipped = 0
            
            for doc_config in config.documents:
                try:
                    # Check if document already exists
                    existing = await self.database.context_documents.get_by_name(doc_config.name)
                    if existing:
                        self.log_progress(f"Document '{doc_config.name}' already exists, skipping")
                        docs_skipped += 1
                        continue
                    
                    # Get document content
                    try:
                        content = config.get_document_content(doc_config)
                    except Exception as e:
                        self.log_progress(f"Failed to load content for '{doc_config.name}': {e}", success=False)
                        continue
                    
                    # Create document entity
                    document = ContextEntity(
                        name=doc_config.name,
                        title=doc_config.title,
                        category=doc_config.category,
                        content=content
                    )
                    
                    doc_id = await self.database.context_documents.create(document)
                    self.log_progress(f"Added document '{doc_config.name}' (ID: {doc_id})")
                    docs_added += 1
                    
                except Exception as e:
                    self.log_progress(f"Failed to add document '{doc_config.name}': {e}", success=False)
                    return False
            
            print(f"📚 Document seeding complete: {docs_added} added, {docs_skipped} skipped")
            return True
            
        except Exception as e:
            print(f"❌ Document seeding failed: {e}")
            return False


class SystemSeeder:
    """Main seeder orchestrator"""
    
    def __init__(self, database_manager, config_dir: str = "config/seeds"):
        self.database = database_manager
        self.config_dir = config_dir
        
        # Initialize individual seeders
        self.agent_seeder = AgentSeeder(database_manager)
        self.tool_seeder = ToolSeeder(database_manager)
        self.document_seeder = DocumentSeeder(database_manager)
    
    async def seed_all(self) -> bool:
        """Seed all system data from configuration"""
        print("🌱 Starting system seeding from configuration...")
        
        try:
            # Load configuration
            config = SeedConfiguration(self.config_dir)
            if not config.validate_all():
                print("❌ Configuration validation failed")
                return False
            
            # Seed in order: documents first (dependencies), then tools, then agents
            success = True
            
            # 1. Seed documents (agents depend on context documents)
            if not await self.document_seeder.seed(config):
                success = False
            
            # 2. Seed tools (agents depend on available tools)
            if success and not await self.tool_seeder.seed(config):
                success = False
            
            # 3. Seed agents (last, depends on documents and tools)
            if success and not await self.agent_seeder.seed(config):
                success = False
            
            if success:
                print("🌱 System seeding completed successfully!")
            else:
                print("❌ System seeding failed")
            
            return success
            
        except Exception as e:
            print(f"❌ System seeding failed: {e}")
            return False