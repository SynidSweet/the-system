from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from config.database import db_manager
from .models import (
    Agent, Task, Message, Tool, ContextDocument, SystemEvent, UserMessage,
    TaskStatus, MessageType, AgentStatus, ToolStatus, EventSeverity, UserMessageType, MessagePriority,
    serialize_for_db, deserialize_from_db
)


class AgentRepository:
    async def create(self, agent: Agent) -> int:
        """Create a new agent"""
        query = """
        INSERT INTO agents (name, version, instruction, context_documents, available_tools, 
                          permissions, model_config, created_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            agent.name,
            agent.version,
            agent.instruction,
            serialize_for_db(agent.context_documents),
            serialize_for_db(agent.available_tools),
            serialize_for_db(agent.permissions),
            serialize_for_db(agent.llm_config),
            agent.created_by,
            agent.status.value
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        query = "SELECT * FROM agents WHERE id = ?"
        results = await db_manager.execute_query(query, (agent_id,))
        if not results:
            return None
        
        row = results[0]
        return Agent(
            id=row['id'],
            name=row['name'],
            version=row['version'],
            instruction=row['instruction'],
            context_documents=deserialize_from_db(row['context_documents']) or [],
            available_tools=deserialize_from_db(row['available_tools']) or [],
            permissions=deserialize_from_db(row['permissions'], dict),
            llm_config=deserialize_from_db(row['model_config'], dict),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by'],
            status=AgentStatus(row['status'])
        )
    
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        query = "SELECT * FROM agents WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        if not results:
            return None
        return await self._row_to_agent(results[0])
    
    async def get_all_active(self) -> List[Agent]:
        """Get all active agents"""
        query = "SELECT * FROM agents WHERE status = 'active' ORDER BY name"
        results = await db_manager.execute_query(query)
        return [await self._row_to_agent(row) for row in results]
    
    async def update(self, agent: Agent) -> bool:
        """Update an existing agent"""
        query = """
        UPDATE agents SET name = ?, version = ?, instruction = ?, context_documents = ?,
                         available_tools = ?, permissions = ?, 
                         model_config = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        params = (
            agent.name,
            agent.version,
            agent.instruction,
            serialize_for_db(agent.context_documents),
            serialize_for_db(agent.available_tools),
            serialize_for_db(agent.permissions),
            serialize_for_db(agent.llm_config),
            agent.status.value,
            agent.id
        )
        rowid = await db_manager.execute_command(query, params)
        return rowid is not None
    
    async def _row_to_agent(self, row: Dict[str, Any]) -> Agent:
        """Convert database row to Agent object"""
        return Agent(
            id=row['id'],
            name=row['name'],
            version=row['version'],
            instruction=row['instruction'],
            context_documents=deserialize_from_db(row['context_documents']) or [],
            available_tools=deserialize_from_db(row['available_tools']) or [],
            permissions=deserialize_from_db(row['permissions'], dict),
            llm_config=deserialize_from_db(row['model_config'], dict),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by'],
            status=AgentStatus(row['status'])
        )


class TaskRepository:
    async def create(self, task: Task) -> int:
        """Create a new task"""
        query = """
        INSERT INTO tasks (parent_task_id, tree_id, agent_id, instruction, status, 
                          priority, max_execution_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            task.parent_task_id,
            task.tree_id,
            task.agent_id,
            task.instruction,
            task.status.value,
            task.priority,
            task.max_execution_time
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        query = "SELECT * FROM tasks WHERE id = ?"
        results = await db_manager.execute_query(query, (task_id,))
        if not results:
            return None
        return self._row_to_task(results[0])
    
    async def get_by_tree_id(self, tree_id: int) -> List[Task]:
        """Get all tasks in a tree"""
        query = "SELECT * FROM tasks WHERE tree_id = ? ORDER BY created_at"
        results = await db_manager.execute_query(query, (tree_id,))
        return [self._row_to_task(row) for row in results]
    
    async def get_children(self, parent_task_id: int) -> List[Task]:
        """Get child tasks"""
        query = "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at"
        results = await db_manager.execute_query(query, (parent_task_id,))
        return [self._row_to_task(row) for row in results]
    
    async def get_active_tasks(self) -> List[Task]:
        """Get all active tasks"""
        query = "SELECT * FROM active_tasks ORDER BY priority DESC, created_at"
        results = await db_manager.execute_query(query)
        return [self._row_to_task(row) for row in results]
    
    async def get_all_root_tasks(self) -> List[Task]:
        """Get all root tasks (tasks with no parent)"""
        query = """
        SELECT * FROM tasks 
        WHERE parent_task_id IS NULL 
        ORDER BY created_at DESC
        LIMIT 100
        """
        results = await db_manager.execute_query(query)
        return [self._row_to_task(row) for row in results]
    
    async def update_status(self, task_id: int, status: TaskStatus, 
                           result: str = None, summary: str = None, 
                           error_message: str = None) -> bool:
        """Update task status and results"""
        query = """
        UPDATE tasks SET status = ?, result = ?, summary = ?, error_message = ?,
                        started_at = CASE WHEN ? = 'running' AND started_at IS NULL 
                                         THEN CURRENT_TIMESTAMP ELSE started_at END,
                        completed_at = CASE WHEN ? IN ('complete', 'failed') 
                                           THEN CURRENT_TIMESTAMP ELSE completed_at END
        WHERE id = ?
        """
        params = (status.value, result, summary, error_message, status.value, status.value, task_id)
        rowid = await db_manager.execute_command(query, params)
        return rowid is not None
    
    async def get_next_tree_id(self) -> int:
        """Get next available tree ID"""
        query = "SELECT COALESCE(MAX(tree_id), 0) + 1 as next_id FROM tasks"
        results = await db_manager.execute_query(query)
        return results[0]['next_id']
    
    def _row_to_task(self, row: Dict[str, Any]) -> Task:
        """Convert database row to Task object"""
        return Task(
            id=row['id'],
            parent_task_id=row['parent_task_id'],
            tree_id=row['tree_id'],
            agent_id=row['agent_id'],
            instruction=row['instruction'],
            status=TaskStatus(row['status']),
            result=row['result'],
            summary=row['summary'],
            error_message=row['error_message'],
            priority=row['priority'],
            max_execution_time=row['max_execution_time'],
            created_at=row['created_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at']
        )


class MessageRepository:
    async def create(self, message: Message) -> int:
        """Create a new message"""
        query = """
        INSERT INTO messages (task_id, message_type, content, metadata, 
                             parent_message_id, token_count, execution_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            message.task_id,
            message.message_type.value,
            message.content,
            serialize_for_db(message.metadata),
            message.parent_message_id,
            message.token_count,
            message.execution_time_ms
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_task_id(self, task_id: int) -> List[Message]:
        """Get all messages for a task"""
        query = "SELECT * FROM messages WHERE task_id = ? ORDER BY timestamp"
        results = await db_manager.execute_query(query, (task_id,))
        return [self._row_to_message(row) for row in results]
    
    async def get_recent_messages(self, limit: int = 100) -> List[Message]:
        """Get recent messages across all tasks"""
        query = "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?"
        results = await db_manager.execute_query(query, (limit,))
        return [self._row_to_message(row) for row in results]
    
    def _row_to_message(self, row: Dict[str, Any]) -> Message:
        """Convert database row to Message object"""
        return Message(
            id=row['id'],
            task_id=row['task_id'],
            message_type=MessageType(row['message_type']),
            content=row['content'],
            metadata=deserialize_from_db(row['metadata']) or {},
            parent_message_id=row['parent_message_id'],
            timestamp=row['timestamp'],
            token_count=row['token_count'],
            execution_time_ms=row['execution_time_ms']
        )


class ContextDocumentRepository:
    async def create(self, doc: ContextDocument) -> int:
        """Create a new context document"""
        query = """
        INSERT INTO context_documents (name, title, content, format, metadata, 
                                     version, category, access_level, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            doc.name,
            doc.title,
            doc.content,
            doc.format,
            serialize_for_db(doc.metadata),
            doc.version,
            doc.category,
            doc.access_level,
            doc.updated_by
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_name(self, name: str) -> Optional[ContextDocument]:
        """Get context document by name"""
        query = "SELECT * FROM context_documents WHERE name = ?"
        results = await db_manager.execute_query(query, (name,))
        if not results:
            return None
        return self._row_to_document(results[0])
    
    async def get_by_names(self, names: List[str]) -> List[ContextDocument]:
        """Get multiple context documents by name"""
        if not names:
            return []
        
        placeholders = ','.join(['?' for _ in names])
        query = f"SELECT * FROM context_documents WHERE name IN ({placeholders})"
        results = await db_manager.execute_query(query, tuple(names))
        return [self._row_to_document(row) for row in results]
    
    async def update_content(self, name: str, content: str, updated_by: int = None) -> bool:
        """Update document content"""
        query = """
        UPDATE context_documents SET content = ?, updated_by = ?, 
                                   updated_at = CURRENT_TIMESTAMP
        WHERE name = ?
        """
        rowid = await db_manager.execute_command(query, (content, updated_by, name))
        return rowid is not None
    
    def _row_to_document(self, row: Dict[str, Any]) -> ContextDocument:
        """Convert database row to ContextDocument object"""
        return ContextDocument(
            id=row['id'],
            name=row['name'],
            title=row['title'],
            content=row['content'],
            format=row['format'],
            metadata=deserialize_from_db(row['metadata']) or {},
            version=row['version'],
            category=row['category'],
            access_level=row['access_level'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            updated_by=row['updated_by']
        )


class ToolRepository:
    async def create(self, tool: Tool) -> int:
        """Create a new tool"""
        query = """
        INSERT INTO tools (name, version, description, category, implementation, 
                          parameters, permissions, dependencies, created_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            tool.name,
            tool.version,
            tool.description,
            tool.category,
            serialize_for_db(tool.implementation),
            serialize_for_db(tool.parameters),
            serialize_for_db(tool.permissions),
            serialize_for_db(tool.dependencies),
            tool.created_by,
            tool.status.value
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_name(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        query = "SELECT * FROM tools WHERE name = ? AND status = 'active'"
        results = await db_manager.execute_query(query, (name,))
        if not results:
            return None
        return self._row_to_tool(results[0])
    
    async def get_by_names(self, names: List[str]) -> List[Tool]:
        """Get multiple tools by name"""
        if not names:
            return []
        
        placeholders = ','.join(['?' for _ in names])
        query = f"SELECT * FROM tools WHERE name IN ({placeholders}) AND status = 'active'"
        results = await db_manager.execute_query(query, tuple(names))
        return [self._row_to_tool(row) for row in results]
    
    async def get_all_active(self) -> List[Tool]:
        """Get all active tools"""
        query = "SELECT * FROM tools WHERE status = 'active' ORDER BY category, name"
        results = await db_manager.execute_query(query)
        return [self._row_to_tool(row) for row in results]
    
    def _row_to_tool(self, row: Dict[str, Any]) -> Tool:
        """Convert database row to Tool object"""
        return Tool(
            id=row['id'],
            name=row['name'],
            version=row['version'],
            description=row['description'],
            category=row['category'],
            implementation=deserialize_from_db(row['implementation'], dict),
            parameters=deserialize_from_db(row['parameters']) or {},
            permissions=deserialize_from_db(row['permissions']) or [],
            dependencies=deserialize_from_db(row['dependencies']) or [],
            created_at=row['created_at'],
            created_by=row['created_by'],
            status=ToolStatus(row['status'])
        )


class SystemEventRepository:
    async def create(self, event: SystemEvent) -> int:
        """Create a new system event"""
        query = """
        INSERT INTO system_events (event_type, source_task_id, event_data, severity)
        VALUES (?, ?, ?, ?)
        """
        params = (
            event.event_type,
            event.source_task_id,
            serialize_for_db(event.event_data),
            event.severity.value
        )
        return await db_manager.execute_command(query, params)
    
    async def get_recent_events(self, limit: int = 100) -> List[SystemEvent]:
        """Get recent system events"""
        query = "SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?"
        results = await db_manager.execute_query(query, (limit,))
        return [self._row_to_event(row) for row in results]
    
    def _row_to_event(self, row: Dict[str, Any]) -> SystemEvent:
        """Convert database row to SystemEvent object"""
        return SystemEvent(
            id=row['id'],
            event_type=row['event_type'],
            source_task_id=row['source_task_id'],
            event_data=deserialize_from_db(row['event_data']) or {},
            timestamp=row['timestamp'],
            severity=EventSeverity(row['severity'])
        )


class UserMessageRepository:
    async def create(self, user_message: Dict[str, Any]) -> int:
        """Create a new user message"""
        query = """
        INSERT INTO user_messages (task_id, agent_name, message, message_type, priority, 
                                 requires_response, suggested_actions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_message.get('task_id'),
            user_message.get('agent_name', 'system'),
            user_message['message'],
            user_message.get('message_type', 'info'),
            user_message.get('priority', 'normal'),
            user_message.get('requires_response', False),
            serialize_for_db(user_message.get('suggested_actions', []))
        )
        return await db_manager.execute_command(query, params)
    
    async def get_by_id(self, message_id: int) -> Optional[UserMessage]:
        """Get user message by ID"""
        query = "SELECT * FROM user_messages WHERE id = ?"
        results = await db_manager.execute_query(query, (message_id,))
        if not results:
            return None
        return self._row_to_user_message(results[0])
    
    async def get_unread_messages(self, limit: int = 50) -> List[UserMessage]:
        """Get unread user messages"""
        query = "SELECT * FROM user_messages WHERE read_at IS NULL ORDER BY timestamp DESC LIMIT ?"
        results = await db_manager.execute_query(query, (limit,))
        return [self._row_to_user_message(row) for row in results]
    
    async def get_recent_messages(self, limit: int = 100) -> List[UserMessage]:
        """Get recent user messages"""
        query = "SELECT * FROM user_messages ORDER BY timestamp DESC LIMIT ?"
        results = await db_manager.execute_query(query, (limit,))
        return [self._row_to_user_message(row) for row in results]
    
    async def get_messages_by_task(self, task_id: int) -> List[UserMessage]:
        """Get all user messages for a specific task"""
        query = "SELECT * FROM user_messages WHERE task_id = ? ORDER BY timestamp ASC"
        results = await db_manager.execute_query(query, (task_id,))
        return [self._row_to_user_message(row) for row in results]
    
    async def mark_as_read(self, message_id: int) -> bool:
        """Mark a user message as read"""
        query = "UPDATE user_messages SET read_at = CURRENT_TIMESTAMP WHERE id = ?"
        return await db_manager.execute_command(query, (message_id,)) > 0
    
    async def add_user_response(self, message_id: int, response: str) -> bool:
        """Add user response to a message"""
        query = """
        UPDATE user_messages 
        SET user_response = ?, responded_at = CURRENT_TIMESTAMP, read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
        WHERE id = ?
        """
        return await db_manager.execute_command(query, (response, message_id)) > 0
    
    async def get_pending_responses(self) -> List[UserMessage]:
        """Get messages that require response but haven't been responded to"""
        query = """
        SELECT * FROM user_messages 
        WHERE requires_response = TRUE AND user_response IS NULL 
        ORDER BY priority DESC, timestamp ASC
        """
        results = await db_manager.execute_query(query)
        return [self._row_to_user_message(row) for row in results]
    
    def _row_to_user_message(self, row: Dict[str, Any]) -> UserMessage:
        """Convert database row to UserMessage object"""
        return UserMessage(
            id=row['id'],
            task_id=row['task_id'],
            agent_name=row['agent_name'],
            message=row['message'],
            message_type=UserMessageType(row['message_type']),
            priority=MessagePriority(row['priority']),
            requires_response=bool(row['requires_response']),
            suggested_actions=deserialize_from_db(row['suggested_actions']) or [],
            timestamp=row['timestamp'],
            read_at=row['read_at'],
            responded_at=row['responded_at'],
            user_response=row['user_response']
        )


class DatabaseManager:
    """Unified database manager with all repositories"""
    
    def __init__(self):
        self.agents = AgentRepository()
        self.tasks = TaskRepository()
        self.messages = MessageRepository()
        self.context_documents = ContextDocumentRepository()
        self.tools = ToolRepository()
        self.system_events = SystemEventRepository()
        self.user_messages = UserMessageRepository()
    
    async def initialize(self):
        """Initialize database connection"""
        await db_manager.connect()
    
    async def close(self):
        """Close database connection"""
        await db_manager.disconnect()


# Global database manager instance
database = DatabaseManager()