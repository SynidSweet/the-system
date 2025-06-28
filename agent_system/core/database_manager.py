"""
Database manager module for the agent system.
Provides centralized database access and repository pattern implementation.
"""

from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from config.database import db_manager


class AgentRepository:
    """Repository for agent-related database operations"""
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name"""
        query = "SELECT * FROM agents WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        return results[0] if results else None
    
    async def get_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        query = "SELECT * FROM agents WHERE id = ?"
        results = await db_manager.execute_query(query, (agent_id,))
        return results[0] if results else None
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active agents"""
        query = "SELECT * FROM agents"
        results = await db_manager.execute_query(query)
        return results if results else []
    
    async def create(self, **kwargs) -> str:
        """Create a new agent"""
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO agents ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')


class TaskRepository:
    """Repository for task-related database operations"""
    
    async def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        query = "SELECT * FROM tasks WHERE id = ?"
        results = await db_manager.execute_query(query, (task_id,))
        return results[0] if results else None
    
    async def get_by_tree_id(self, tree_id: str) -> List[Dict[str, Any]]:
        """Get all tasks in a tree"""
        query = "SELECT * FROM tasks WHERE tree_id = ? ORDER BY id"
        results = await db_manager.execute_query(query, (tree_id,))
        return results if results else []
    
    async def create(self, **kwargs) -> str:
        """Create a new task"""
        # Handle JSON serialization for context and metadata
        if 'context' in kwargs and isinstance(kwargs['context'], dict):
            kwargs['context'] = json.dumps(kwargs['context'])
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            kwargs['metadata'] = json.dumps(kwargs['metadata'])
        if 'result' in kwargs and kwargs['result'] is not None and isinstance(kwargs['result'], dict):
            kwargs['result'] = json.dumps(kwargs['result'])
            
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')
    
    async def update(self, task_id: str, **kwargs) -> None:
        """Update a task"""
        # Handle JSON serialization
        if 'context' in kwargs and isinstance(kwargs['context'], dict):
            kwargs['context'] = json.dumps(kwargs['context'])
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            kwargs['metadata'] = json.dumps(kwargs['metadata'])
        if 'result' in kwargs and kwargs['result'] is not None and isinstance(kwargs['result'], dict):
            kwargs['result'] = json.dumps(kwargs['result'])
            
        set_clauses = [f"{col} = ?" for col in kwargs.keys()]
        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        values = list(kwargs.values()) + [task_id]
        await db_manager.execute_command(query, values)
    
    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks"""
        query = "SELECT * FROM tasks WHERE status = 'pending' ORDER BY id"
        results = await db_manager.execute_query(query)
        return results if results else []
    
    async def get_all_root_tasks(self) -> List[Dict[str, Any]]:
        """Get all root tasks (tasks with no parent)"""
        query = "SELECT * FROM tasks WHERE parent_task_id IS NULL ORDER BY id DESC"
        results = await db_manager.execute_query(query)
        return results if results else []
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks (running, queued, created)"""
        query = "SELECT * FROM tasks WHERE status IN ('running', 'queued', 'created') ORDER BY id DESC"
        results = await db_manager.execute_query(query)
        return results if results else []


class MessageRepository:
    """Repository for message-related database operations"""
    
    async def create(self, **kwargs) -> str:
        """Create a new message"""
        # Handle JSON serialization for metadata
        if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
            kwargs['metadata'] = json.dumps(kwargs['metadata'])
            
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO messages ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')
    
    async def get_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a task"""
        query = "SELECT * FROM messages WHERE task_id = ? ORDER BY timestamp"
        results = await db_manager.execute_query(query, (task_id,))
        return results if results else []


class ToolRepository:
    """Repository for tool-related database operations"""
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active tools"""
        query = "SELECT * FROM tools"
        results = await db_manager.execute_query(query)
        return results if results else []
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool by name"""
        query = "SELECT * FROM tools WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        return results[0] if results else None
    
    async def get_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """Get tools by multiple names"""
        if not names:
            return []
        placeholders = ",".join(["?" for _ in names])
        query = f"SELECT * FROM tools WHERE name IN ({placeholders})"
        results = await db_manager.execute_query(query, names)
        return results if results else []
    
    async def create(self, **kwargs) -> str:
        """Create a new tool"""
        # Handle JSON serialization
        if 'parameters' in kwargs and isinstance(kwargs['parameters'], dict):
            kwargs['parameters'] = json.dumps(kwargs['parameters'])
        if 'permissions' in kwargs and isinstance(kwargs['permissions'], dict):
            kwargs['permissions'] = json.dumps(kwargs['permissions'])
            
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO tools ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')


class ContextDocumentRepository:
    """Repository for context document operations"""
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all context documents"""
        query = "SELECT * FROM context_documents ORDER BY created_at"
        results = await db_manager.execute_query(query)
        return results if results else []
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get documents by category"""
        query = "SELECT * FROM context_documents WHERE category = ? ORDER BY created_at"
        results = await db_manager.execute_query(query, (category,))
        return results if results else []
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get document by name"""
        query = "SELECT * FROM context_documents WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        return results[0] if results else None
    
    async def get_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """Get documents by multiple names"""
        if not names:
            return []
        placeholders = ",".join(["?" for _ in names])
        query = f"SELECT * FROM context_documents WHERE name IN ({placeholders})"
        results = await db_manager.execute_query(query, names)
        return results if results else []
    
    async def create(self, **kwargs) -> str:
        """Create a new context document"""
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO context_documents ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')


class ProcessRepository:
    """Repository for process-related database operations"""
    
    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get process by name"""
        query = "SELECT * FROM processes WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        return results[0] if results else None
    
    async def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active processes"""
        query = "SELECT * FROM processes WHERE status = 'active'"
        results = await db_manager.execute_query(query)
        return results if results else []


class EventRepository:
    """Repository for event-related database operations"""
    
    async def create(self, **kwargs) -> str:
        """Create a new event"""
        # Handle JSON serialization
        if 'data' in kwargs and isinstance(kwargs['data'], dict):
            kwargs['data'] = json.dumps(kwargs['data'])
            
        columns = list(kwargs.keys())
        placeholders = ["?" for _ in columns]
        query = f"INSERT INTO events ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        values = [kwargs[col] for col in columns]
        await db_manager.execute_command(query, values)
        return kwargs.get('id')


class DatabaseManager:
    """Main database manager providing access to all repositories"""
    
    def __init__(self):
        self.agents = AgentRepository()
        self.tasks = TaskRepository()
        self.messages = MessageRepository()
        self.tools = ToolRepository()
        self.context_documents = ContextDocumentRepository()
        self.processes = ProcessRepository()
        self.events = EventRepository()
    
    async def initialize(self):
        """Initialize database connection"""
        # Database initialization is handled by db_manager
        await db_manager.connect()
    
    async def disconnect(self):
        """Close database connection"""
        await db_manager.disconnect()
    
    async def execute_command(self, query: str, params: tuple = None):
        """Execute a database command (INSERT, UPDATE, DELETE)"""
        return await db_manager.execute_command(query, params)
    
    async def execute_query(self, query: str, params: tuple = None):
        """Execute a database query (SELECT)"""
        return await db_manager.execute_query(query, params)


# Global database instance
database = DatabaseManager()