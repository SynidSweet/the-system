"""
Minimal database configuration for entity-based architecture.

All database schema is managed through migrations in the database/migrations directory.
This file only provides connection management.
"""

import aiosqlite
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from .settings import settings


class DatabaseManager:
    """Manages database connections for the entity-based system."""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.database_url.replace("sqlite:///", "")
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Initialize database connection"""
        self._connection = await aiosqlite.connect(self.db_url)
        self._connection.row_factory = aiosqlite.Row
        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")
    
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
    
    async def execute_script(self, script: str):
        """Execute a SQL script (multiple statements)"""
        async with self.get_connection() as conn:
            await conn.executescript(script)
            await conn.commit()
    
    async def get_schema_version(self) -> int:
        """Get current schema version from migrations table"""
        try:
            result = await self.execute_query(
                "SELECT MAX(version) as version FROM schema_migrations WHERE applied = 1"
            )
            return result[0]['version'] if result and result[0]['version'] else 0
        except:
            # Table doesn't exist yet
            return 0
    
    async def apply_migrations(self):
        """Apply any pending migrations"""
        # This would be implemented to run migrations from database/migrations/
        # For now, migrations are applied manually
        pass


# Global database manager instance
db_manager = DatabaseManager()