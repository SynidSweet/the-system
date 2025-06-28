"""Entity Manager MCP Server - Core CRUD operations for all entity types."""

import json
import logging
from typing import Dict, Any, List, Optional

from .base import MCPServer, PermissionError
from core.entities.entity_manager import EntityManager
from core.permissions.manager import DatabasePermissionManager
from core.events.event_types import EntityType

logger = logging.getLogger(__name__)


class EntityManagerMCP(MCPServer):
    """MCP server providing entity CRUD operations."""
    
    def __init__(self, entity_manager: EntityManager, permission_manager: DatabasePermissionManager):
        super().__init__("entity_manager", permission_manager)
        self.entity_manager = entity_manager
        
    def register_tools(self):
        """Register essential entity management tools."""
        # Core CRUD operations
        self.register_tool("create_entity", self.create_entity)
        self.register_tool("get_entity", self.get_entity)
        self.register_tool("update_entity", self.update_entity)
        self.register_tool("delete_entity", self.delete_entity)
        self.register_tool("list_entities", self.list_entities)
        
        # Specialized entity creation
        self.register_tool("create_agent", self.create_agent)
        self.register_tool("create_task", self.create_task)
        self.register_tool("update_task", self.update_task)
        self.register_tool("create_document", self.create_document)
        
    # Agent Management Tools
    
    async def get_agent(self, agent_id: int, agent_type: str, task_id: int) -> Dict[str, Any]:
        """Get agent by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "agent"):
            raise PermissionError("Insufficient permissions to read agent")
        
        agent = await self.entity_manager.get_entity(EntityType.AGENT, agent_id)
        
        if not agent:
            return None
            
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "instruction": agent.instruction,
            "context_documents": agent.context_documents,
            "available_tools": agent.available_tools,
            "metadata": agent.metadata
        }
    
    async def update_agent(self, agent_id: int, updates: Dict[str, Any], 
                          agent_type: str, task_id: int) -> bool:
        """Update agent configuration."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "agent"):
            raise PermissionError("Insufficient permissions to update agent")
        
        # Get existing agent
        agent = await self.entity_manager.get_entity(EntityType.AGENT, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Update allowed fields
        allowed_fields = ["instruction", "description", "context_documents", "available_tools", "metadata"]
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(agent, field, value)
        
        # Save changes
        success = await self.entity_manager.update_entity(agent)
        
        if success:
            logger.info(f"Updated agent {agent_id}")
            
        return success
    
    async def create_agent(self, config: Dict[str, Any], agent_type: str, task_id: int) -> int:
        """Create new agent."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "agent"):
            raise PermissionError("Insufficient permissions to create agent")
        
        from core.entities.agent_entity import AgentEntity
        
        agent = AgentEntity(
            id=0,  # Will be assigned by database
            entity_type=EntityType.AGENT,
            name=config["name"],
            description=config.get("description", ""),
            metadata=config.get("metadata", {}),
            instruction=config["instruction"],
            context_documents=config.get("context_documents", []),
            available_tools=config.get("available_tools", [])
        )
        
        new_id = await self.entity_manager.create_entity(agent)
        logger.info(f"Created agent {new_id}")
        
        return new_id
    
    async def list_agents(self, filters: Optional[Dict[str, Any]] = None, 
                         agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """List agents with optional filters."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "agent"):
            raise PermissionError("Insufficient permissions to list agents")
        
        agents = await self.entity_manager.get_entities_by_type(EntityType.AGENT)
        
        # Apply filters if provided
        if filters:
            # Simple filtering implementation
            filtered = []
            for agent in agents:
                match = True
                for key, value in filters.items():
                    if not hasattr(agent, key) or getattr(agent, key) != value:
                        match = False
                        break
                if match:
                    filtered.append(agent)
            agents = filtered
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            }
            for agent in agents
        ]
    
    # Task Management Tools
    
    async def get_task(self, task_id: int, agent_type: str = None, task_id_ctx: int = None) -> Dict[str, Any]:
        """Get task by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id_ctx, "read", "task"):
            raise PermissionError("Insufficient permissions to read task")
        
        task = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        
        if not task:
            return None
            
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "instruction": task.instruction,
            "status": task.status,
            "assigned_agent": task.assigned_agent,
            "parent_task_id": task.parent_task_id,
            "dependencies": task.dependencies,
            "metadata": task.metadata
        }
    
    async def update_task(self, task_id: int, updates: Dict[str, Any],
                         agent_type: str, task_id_ctx: int) -> bool:
        """Update task details."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id_ctx, "write", "task"):
            raise PermissionError("Insufficient permissions to update task")
        
        task = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update allowed fields
        allowed_fields = ["status", "assigned_agent", "metadata", "result"]
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(task, field, value)
        
        success = await self.entity_manager.update_entity(task)
        
        if success:
            logger.info(f"Updated task {task_id}")
            
        return success
    
    async def create_task(self, instruction: str, parent_task_id: Optional[int] = None,
                         agent_type: str = None, task_id: int = None, **kwargs) -> int:
        """Create new task."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "task"):
            raise PermissionError("Insufficient permissions to create task")
        
        from core.entities.task_entity import TaskEntity
        
        task = TaskEntity(
            id=0,  # Will be assigned by database
            entity_type=EntityType.TASK,
            name=kwargs.get("name", f"Task: {instruction[:50]}..."),
            description=kwargs.get("description", ""),
            metadata=kwargs.get("metadata", {}),
            instruction=instruction,
            status="created",
            assigned_agent=kwargs.get("assigned_agent"),
            parent_task_id=parent_task_id,
            dependencies=kwargs.get("dependencies", [])
        )
        
        new_id = await self.entity_manager.create_entity(task)
        logger.info(f"Created task {new_id}")
        
        return new_id
    
    async def get_task_dependencies(self, task_id: int, agent_type: str = None, 
                                   task_id_ctx: int = None) -> List[Dict[str, Any]]:
        """Get task dependencies."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id_ctx, "read", "task"):
            raise PermissionError("Insufficient permissions to read task dependencies")
        
        task = await self.entity_manager.get_entity(EntityType.TASK, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        dependencies = []
        for dep_id in task.dependencies:
            dep_task = await self.entity_manager.get_entity(EntityType.TASK, dep_id)
            if dep_task:
                dependencies.append({
                    "id": dep_task.id,
                    "instruction": dep_task.instruction,
                    "status": dep_task.status
                })
        
        return dependencies
    
    # Process Management Tools
    
    async def get_process(self, process_id: int, agent_type: str = None, 
                         task_id: int = None) -> Dict[str, Any]:
        """Get process by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "process"):
            raise PermissionError("Insufficient permissions to read process")
        
        process = await self.entity_manager.get_entity(EntityType.PROCESS, process_id)
        
        if not process:
            return None
            
        return {
            "id": process.id,
            "name": process.name,
            "description": process.description,
            "process_type": process.process_type,
            "trigger_events": process.trigger_events,
            "parameters": process.parameters,
            "metadata": process.metadata
        }
    
    async def list_processes(self, category: Optional[str] = None,
                           agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """List available processes."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "process"):
            raise PermissionError("Insufficient permissions to list processes")
        
        processes = await self.entity_manager.get_entities_by_type(EntityType.PROCESS)
        
        # Filter by category if provided
        if category:
            processes = [p for p in processes if p.metadata.get("category") == category]
        
        return [
            {
                "id": process.id,
                "name": process.name,
                "process_type": process.process_type,
                "description": process.description
            }
            for process in processes
        ]
    
    # Document Management Tools
    
    async def get_document(self, doc_id: int, agent_type: str = None,
                          task_id: int = None) -> Dict[str, Any]:
        """Get document by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "document"):
            raise PermissionError("Insufficient permissions to read document")
        
        doc = await self.entity_manager.get_entity(EntityType.CONTEXT, doc_id)
        
        if not doc:
            return None
            
        return {
            "id": doc.id,
            "name": doc.name,
            "title": doc.title,
            "content": doc.content,
            "category": doc.category,
            "format": doc.format,
            "metadata": doc.metadata
        }
    
    async def create_document(self, name: str, content: str, metadata: Dict[str, Any],
                            agent_type: str = None, task_id: int = None) -> int:
        """Create new document."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "document"):
            raise PermissionError("Insufficient permissions to create document")
        
        from core.entities.context_entity import ContextEntity
        
        doc = ContextEntity(
            id=0,  # Will be assigned by database
            entity_type=EntityType.CONTEXT,
            name=name,
            description=metadata.get("description", ""),
            metadata=metadata,
            title=metadata.get("title", name),
            content=content,
            category=metadata.get("category", "general"),
            format=metadata.get("format", "text")
        )
        
        new_id = await self.entity_manager.create_entity(doc)
        logger.info(f"Created document {new_id}")
        
        return new_id
    
    async def update_document(self, doc_id: int, updates: Dict[str, Any],
                            agent_type: str = None, task_id: int = None) -> bool:
        """Update document content or metadata."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "document"):
            raise PermissionError("Insufficient permissions to update document")
        
        doc = await self.entity_manager.get_entity(EntityType.CONTEXT, doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        
        # Update allowed fields
        allowed_fields = ["content", "title", "category", "metadata"]
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(doc, field, value)
        
        success = await self.entity_manager.update_entity(doc)
        
        if success:
            logger.info(f"Updated document {doc_id}")
            
        return success
    
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None,
                             agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """Search documents by content or metadata."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "document"):
            raise PermissionError("Insufficient permissions to search documents")
        
        docs = await self.entity_manager.get_entities_by_type(EntityType.CONTEXT)
        
        # Simple search implementation
        results = []
        query_lower = query.lower()
        
        for doc in docs:
            # Search in content, title, and name
            if (query_lower in doc.content.lower() or 
                query_lower in doc.title.lower() or 
                query_lower in doc.name.lower()):
                
                # Apply filters if provided
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key == "category" and doc.category != value:
                            match = False
                            break
                        elif key == "format" and doc.format != value:
                            match = False
                            break
                    if not match:
                        continue
                
                results.append({
                    "id": doc.id,
                    "name": doc.name,
                    "title": doc.title,
                    "category": doc.category,
                    "preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                })
        
        return results
    
    # Tool Management Tools
    
    async def get_tool(self, tool_id: int, agent_type: str = None,
                      task_id: int = None) -> Dict[str, Any]:
        """Get tool by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "tool"):
            raise PermissionError("Insufficient permissions to read tool")
        
        tool = await self.entity_manager.get_entity(EntityType.TOOL, tool_id)
        
        if not tool:
            return None
            
        return {
            "id": tool.id,
            "name": tool.name,
            "function_name": tool.function_name,
            "parameters": tool.parameters,
            "returns": tool.returns,
            "metadata": tool.metadata
        }
    
    async def list_tools_entities(self, category: Optional[str] = None,
                                 agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """List tool entities (not MCP tools)."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "tool"):
            raise PermissionError("Insufficient permissions to list tools")
        
        tools = await self.entity_manager.get_entities_by_type(EntityType.TOOL)
        
        # Filter by category if provided
        if category:
            tools = [t for t in tools if t.metadata.get("category") == category]
        
        return [
            {
                "id": tool.id,
                "name": tool.name,
                "function_name": tool.function_name,
                "description": tool.description
            }
            for tool in tools
        ]
    
    # Event Management Tools
    
    async def get_events(self, filters: Dict[str, Any], agent_type: str = None,
                        task_id: int = None) -> List[Dict[str, Any]]:
        """Get events with filters."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", "event"):
            raise PermissionError("Insufficient permissions to read events")
        
        # This would integrate with the event system
        # For now, return empty list
        logger.info(f"Event query with filters: {filters}")
        return []
    
    async def log_event(self, event_type: str, entity_id: int, data: Dict[str, Any],
                       agent_type: str = None, task_id: int = None) -> int:
        """Log a new event."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", "event"):
            raise PermissionError("Insufficient permissions to log events")
        
        # This would integrate with the event system
        logger.info(f"Logging event: {event_type} for entity {entity_id}")
        return 0  # Placeholder event ID
    
    # Relationship Management Tools
    
    async def create_relationship(self, source_type: str, source_id: int,
                                target_type: str, target_id: int,
                                relationship_type: str, metadata: Optional[Dict[str, Any]] = None,
                                agent_type: str = None, task_id: int = None) -> bool:
        """Create relationship between entities."""
        # Check permissions for both entity types
        if not (await self.permission_manager.check_permission(agent_type, task_id, "write", source_type.lower()) and
                await self.permission_manager.check_permission(agent_type, task_id, "write", target_type.lower())):
            raise PermissionError("Insufficient permissions to create relationship")
        
        success = await self.entity_manager.create_relationship(
            source_type=EntityType[source_type.upper()],
            source_id=source_id,
            target_type=EntityType[target_type.upper()],
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {}
        )
        
        if success:
            logger.info(f"Created relationship: {source_type}:{source_id} -> {target_type}:{target_id}")
            
        return success
    
    async def get_relationships(self, entity_type: str, entity_id: int,
                              direction: str = "both", relationship_type: Optional[str] = None,
                              agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """Get relationships for an entity."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", entity_type.lower()):
            raise PermissionError("Insufficient permissions to read relationships")
        
        relationships = await self.entity_manager.get_relationships(
            entity_type=EntityType[entity_type.upper()],
            entity_id=entity_id,
            direction=direction,
            relationship_type=relationship_type
        )
        
        return [
            {
                "source_type": rel["source_type"],
                "source_id": rel["source_id"],
                "target_type": rel["target_type"],
                "target_id": rel["target_id"],
                "relationship_type": rel["relationship_type"],
                "metadata": rel["metadata"]
            }
            for rel in relationships
        ]
    
    # Core CRUD operations
    
    async def create_entity(self, entity_type: str, data: Dict[str, Any],
                          agent_type: str = None, task_id: int = None) -> int:
        """Create any type of entity."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", entity_type.lower()):
            raise PermissionError(f"Insufficient permissions to create {entity_type}")
        
        # Delegate to specific creation methods based on type
        if entity_type.upper() == "AGENT":
            return await self.create_agent(data, agent_type, task_id)
        elif entity_type.upper() == "TASK":
            return await self.create_task(data.get("instruction", ""), 
                                        data.get("parent_task_id"), 
                                        agent_type, task_id, **data)
        elif entity_type.upper() == "CONTEXT":
            return await self.create_document(data.get("name", ""),
                                            data.get("content", ""),
                                            data.get("metadata", {}),
                                            agent_type, task_id)
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")
    
    async def get_entity(self, entity_type: str, entity_id: int,
                       agent_type: str = None, task_id: int = None) -> Dict[str, Any]:
        """Get any type of entity by ID."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", entity_type.lower()):
            raise PermissionError(f"Insufficient permissions to read {entity_type}")
        
        # Delegate to specific get methods based on type
        if entity_type.upper() == "AGENT":
            return await self.get_agent(entity_id, agent_type, task_id)
        elif entity_type.upper() == "TASK":
            return await self.get_task(entity_id, agent_type, task_id)
        elif entity_type.upper() == "CONTEXT":
            return await self.get_document(entity_id, agent_type, task_id)
        elif entity_type.upper() == "PROCESS":
            return await self.get_process(entity_id, agent_type, task_id)
        elif entity_type.upper() == "TOOL":
            return await self.get_tool(entity_id, agent_type, task_id)
        else:
            # For other types, get directly from entity manager
            entity = await self.entity_manager.get_entity(EntityType[entity_type.upper()], entity_id)
            if entity:
                return {
                    "id": entity.id,
                    "name": entity.name,
                    "description": entity.description,
                    "metadata": entity.metadata
                }
            return None
    
    async def update_entity(self, entity_type: str, entity_id: int, updates: Dict[str, Any],
                          agent_type: str = None, task_id: int = None) -> bool:
        """Update any type of entity."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "write", entity_type.lower()):
            raise PermissionError(f"Insufficient permissions to update {entity_type}")
        
        # Delegate to specific update methods based on type
        if entity_type.upper() == "AGENT":
            return await self.update_agent(entity_id, updates, agent_type, task_id)
        elif entity_type.upper() == "TASK":
            return await self.update_task(entity_id, updates, agent_type, task_id)
        elif entity_type.upper() == "CONTEXT":
            return await self.update_document(entity_id, updates, agent_type, task_id)
        else:
            # For other types, update directly via entity manager
            entity = await self.entity_manager.get_entity(EntityType[entity_type.upper()], entity_id)
            if not entity:
                raise ValueError(f"{entity_type} {entity_id} not found")
            
            # Update basic fields
            for field in ["name", "description", "metadata"]:
                if field in updates:
                    setattr(entity, field, updates[field])
            
            return await self.entity_manager.update_entity(entity)
    
    async def delete_entity(self, entity_type: str, entity_id: int,
                          agent_type: str = None, task_id: int = None) -> bool:
        """Delete any type of entity."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "delete", entity_type.lower()):
            raise PermissionError(f"Insufficient permissions to delete {entity_type}")
        
        # Use entity manager to delete
        success = await self.entity_manager.delete_entity(EntityType[entity_type.upper()], entity_id)
        
        if success:
            logger.info(f"Deleted {entity_type} {entity_id}")
            
        return success
    
    async def list_entities(self, entity_type: str, filters: Optional[Dict[str, Any]] = None,
                          agent_type: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """List entities of any type."""
        # Check permissions
        if not await self.permission_manager.check_permission(agent_type, task_id, "read", entity_type.lower()):
            raise PermissionError(f"Insufficient permissions to list {entity_type}")
        
        # Delegate to specific list methods based on type
        if entity_type.upper() == "AGENT":
            return await self.list_agents(filters, agent_type, task_id)
        elif entity_type.upper() == "PROCESS":
            return await self.list_processes(filters.get("category") if filters else None, agent_type, task_id)
        elif entity_type.upper() == "TOOL":
            return await self.list_tools_entities(filters.get("category") if filters else None, agent_type, task_id)
        else:
            # For other types, get all from entity manager
            entities = await self.entity_manager.get_entities_by_type(EntityType[entity_type.upper()])
            
            # Apply basic filters
            if filters:
                filtered = []
                for entity in entities:
                    match = True
                    for key, value in filters.items():
                        if hasattr(entity, key) and getattr(entity, key) != value:
                            match = False
                            break
                    if match:
                        filtered.append(entity)
                entities = filtered
            
            return [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "description": entity.description,
                    "created_at": entity.created_at.isoformat() if hasattr(entity, 'created_at') and entity.created_at else None
                }
                for entity in entities
            ]