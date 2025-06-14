import sqlite3
import asyncio
import aiosqlite
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from .settings import settings


class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.database_url.replace("sqlite:///", "")
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Initialize database connection and create schema if needed"""
        self._connection = await aiosqlite.connect(self.db_url)
        self._connection.row_factory = aiosqlite.Row
        await self.create_schema()
    
    async def disconnect(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection context manager"""
        if not self._connection:
            await self.connect()
        yield self._connection
    
    async def create_schema(self):
        """Create database schema with all tables, indexes, and views"""
        schema_sql = """
        -- Agent Configurations
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0.0',
            instruction TEXT NOT NULL,
            context_documents TEXT, -- JSON array
            available_tools TEXT,   -- JSON array
            permissions TEXT,       -- JSON object
            model_config TEXT,      -- JSON object
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,     -- task_id that created this agent
            status TEXT DEFAULT 'active' -- active, deprecated, testing
        );

        -- Context Documents
        CREATE TABLE IF NOT EXISTS context_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            format TEXT DEFAULT 'markdown',
            metadata TEXT,          -- JSON object
            version TEXT NOT NULL DEFAULT '1.0.0',
            category TEXT NOT NULL,
            access_level TEXT DEFAULT 'internal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER      -- task_id that updated this document
        );

        -- Task Management
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_task_id INTEGER,
            tree_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            instruction TEXT NOT NULL,
            status TEXT DEFAULT 'created',
            result TEXT,
            summary TEXT,
            error_message TEXT,
            priority INTEGER DEFAULT 0,
            max_execution_time INTEGER DEFAULT 300,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        );

        -- Message History
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,          -- JSON object
            parent_message_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            token_count INTEGER,
            execution_time_ms INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_message_id) REFERENCES messages(id)
        );

        -- Tools Registry
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            version TEXT NOT NULL DEFAULT '1.0.0',
            description TEXT,
            category TEXT NOT NULL,
            implementation TEXT NOT NULL, -- JSON object
            parameters TEXT NOT NULL,     -- JSON schema
            permissions TEXT,             -- JSON array
            dependencies TEXT,            -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,           -- task_id that created this tool
            status TEXT DEFAULT 'active'  -- active, deprecated, testing
        );

        -- System Events
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            source_task_id INTEGER,
            event_data TEXT,        -- JSON object
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            severity TEXT DEFAULT 'info' -- debug, info, warning, error, critical
        );

        -- User Messages (Agent-to-User Communication)
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            agent_name TEXT NOT NULL DEFAULT 'system',
            message TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'info', -- question, update, verification, error, info, warning, success
            priority TEXT NOT NULL DEFAULT 'normal',  -- low, normal, high, urgent
            requires_response BOOLEAN DEFAULT FALSE,
            suggested_actions TEXT,    -- JSON array
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP,
            responded_at TIMESTAMP,
            user_response TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_tasks_tree_id ON tasks(tree_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);
        CREATE INDEX IF NOT EXISTS idx_messages_task_id ON messages(task_id);
        CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
        CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_user_messages_task_id ON user_messages(task_id);
        CREATE INDEX IF NOT EXISTS idx_user_messages_type ON user_messages(message_type);
        CREATE INDEX IF NOT EXISTS idx_user_messages_priority ON user_messages(priority);
        CREATE INDEX IF NOT EXISTS idx_user_messages_timestamp ON user_messages(timestamp);

        -- Views for common queries
        CREATE VIEW IF NOT EXISTS active_tasks AS
        SELECT * FROM tasks WHERE status IN ('created', 'queued', 'agent_selected', 'running', 'waiting_subtasks');

        CREATE VIEW IF NOT EXISTS task_trees AS
        SELECT 
            tree_id,
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed_tasks,
            MIN(created_at) as started_at,
            MAX(completed_at) as finished_at
        FROM tasks GROUP BY tree_id;
        """
        
        async with self.get_connection() as conn:
            await conn.executescript(schema_sql)
            await conn.commit()
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def execute_command(self, command: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE command and return lastrowid"""
        async with self.get_connection() as conn:
            cursor = await conn.execute(command, params or ())
            await conn.commit()
            return cursor.lastrowid


# Global database manager instance
db_manager = DatabaseManager()