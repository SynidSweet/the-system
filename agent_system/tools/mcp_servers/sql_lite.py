"""
SQL Lite MCP Server - Provides safe database queries with predefined patterns.

This server implements secure database access with:
- Predefined query templates
- Parameter validation
- Result limiting
- Read-only queries by default
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

from .base import MCPServer
from core.permissions.manager import DatabasePermissionManager


class SQLiteMCPServer(MCPServer):
    """
    MCP server for SQL Lite database operations with security.
    
    Operations:
    - execute_query: Run a predefined query with parameters
    - get_tables: List all tables in database
    - get_schema: Get schema for a specific table
    - get_row_count: Count rows in a table
    - get_recent_records: Get recent records from a table
    - search_records: Search records with pattern matching
    - get_statistics: Get table statistics
    """
    
    # Predefined safe queries
    PREDEFINED_QUERIES = {
        # Task queries
        "get_recent_tasks": """
            SELECT id, parent_task_id, agent_id, instruction, status, 
                   created_at, completed_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT ?
        """,
        
        "get_task_by_status": """
            SELECT id, instruction, status, created_at
            FROM tasks
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """,
        
        "get_task_tree": """
            WITH RECURSIVE task_tree AS (
                SELECT id, parent_task_id, instruction, status, 0 as level
                FROM tasks
                WHERE id = ?
                
                UNION ALL
                
                SELECT t.id, t.parent_task_id, t.instruction, t.status, tt.level + 1
                FROM tasks t
                JOIN task_tree tt ON t.parent_task_id = tt.id
            )
            SELECT * FROM task_tree ORDER BY level, id
        """,
        
        # Agent queries
        "get_agent_performance": """
            SELECT a.name, COUNT(t.id) as task_count,
                   SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed,
                   AVG(JULIANDAY(t.completed_at) - JULIANDAY(t.created_at)) * 24 * 60 as avg_minutes
            FROM agents a
            LEFT JOIN tasks t ON a.id = t.agent_id
            GROUP BY a.id, a.name
        """,
        
        # Event queries
        "get_recent_events": """
            SELECT event_type, entity_type, entity_id, metadata, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """,
        
        "get_events_by_type": """
            SELECT * FROM events
            WHERE event_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
        
        # Tool usage queries
        "get_tool_usage_stats": """
            SELECT tool_name, agent_type, COUNT(*) as usage_count,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                   AVG(execution_time_ms) as avg_time_ms
            FROM tool_usage_events
            WHERE timestamp > datetime('now', '-? days')
            GROUP BY tool_name, agent_type
            ORDER BY usage_count DESC
        """,
        
        # Message queries
        "get_task_messages": """
            SELECT message_type, content, metadata, timestamp
            FROM messages
            WHERE task_id = ?
            ORDER BY timestamp
        """,
        
        # Context queries
        "get_context_usage": """
            SELECT cd.name, cd.title, COUNT(DISTINCT e.entity_id) as usage_count,
                   MAX(e.timestamp) as last_used
            FROM context_documents cd
            JOIN events e ON e.metadata LIKE '%' || cd.name || '%'
            WHERE e.event_type = 'context_accessed'
            GROUP BY cd.id, cd.name, cd.title
            ORDER BY usage_count DESC
        """,
        
        # Entity queries
        "search_entities": """
            SELECT entity_type, entity_id, name, metadata
            FROM entities
            WHERE name LIKE ? OR metadata LIKE ?
            LIMIT ?
        """,
        
        # Relationship queries
        "get_entity_relationships": """
            SELECT er.*, 
                   e1.name as source_name,
                   e2.name as target_name
            FROM entity_relationships er
            JOIN entities e1 ON er.source_type = e1.entity_type 
                            AND er.source_id = e1.entity_id
            JOIN entities e2 ON er.target_type = e2.entity_type 
                            AND er.target_id = e2.entity_id
            WHERE (er.source_type = ? AND er.source_id = ?)
               OR (er.target_type = ? AND er.target_id = ?)
        """
    }
    
    def __init__(
        self,
        permission_manager: DatabasePermissionManager,
        db_path: str,
        read_only: bool = True,
        max_results: int = 1000
    ):
        super().__init__("sqlite", permission_manager)
        
        self.db_path = Path(db_path).resolve()
        if not self.db_path.exists():
            raise ValueError(f"Database not found: {db_path}")
        
        self.read_only = read_only
        self.max_results = max_results
    
    def register_tools(self):
        """Register all SQL tools."""
        self.register_tool("execute_query", self.execute_query)
        self.register_tool("get_tables", self.get_tables)
        self.register_tool("get_schema", self.get_schema)
        self.register_tool("get_row_count", self.get_row_count)
        self.register_tool("get_recent_records", self.get_recent_records)
        self.register_tool("search_records", self.search_records)
        self.register_tool("get_statistics", self.get_statistics)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        if self.read_only:
            # Open in read-only mode
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        else:
            conn = sqlite3.connect(self.db_path)
        
        # Enable row factory for dict-like results
        conn.row_factory = sqlite3.Row
        return conn
    
    def _validate_query_name(self, query_name: str) -> str:
        """Validate and get predefined query."""
        if query_name not in self.PREDEFINED_QUERIES:
            raise ValueError(
                f"Unknown query: {query_name}. "
                f"Available queries: {list(self.PREDEFINED_QUERIES.keys())}"
            )
        
        return self.PREDEFINED_QUERIES[query_name]
    
    def _limit_results(self, results: List[Any]) -> List[Any]:
        """Limit results to max_results."""
        if len(results) > self.max_results:
            print(f"Warning: Results truncated from {len(results)} to {self.max_results}")
            return results[:self.max_results]
        return results
    
    async def execute_query(
        self,
        query_name: str,
        parameters: List[Any] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Execute a predefined query with parameters."""
        try:
            # Get predefined query
            query = self._validate_query_name(query_name)
            
            # Execute query
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            # Fetch results
            results = [dict(row) for row in cursor.fetchall()]
            results = self._limit_results(results)
            
            conn.close()
            
            return {
                "success": True,
                "query_name": query_name,
                "row_count": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query execution failed: {str(e)}"
            }
    
    async def get_tables(
        self,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """List all tables in the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, type 
                FROM sqlite_master 
                WHERE type IN ('table', 'view')
                AND name NOT LIKE 'sqlite_%'
                ORDER BY type, name
            """)
            
            tables = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "table_count": len(tables),
                "tables": tables
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get tables: {str(e)}"
            }
    
    async def get_schema(
        self,
        table_name: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get schema information for a table."""
        try:
            # Validate table name (basic SQL injection prevention)
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [dict(row) for row in cursor.fetchall()]
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = [dict(row) for row in cursor.fetchall()]
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get schema: {str(e)}"
            }
    
    async def get_row_count(
        self,
        table_name: str,
        condition: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get row count for a table with optional condition."""
        try:
            # Validate table name
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if condition:
                # Only allow simple conditions
                allowed_ops = ['=', '>', '<', '>=', '<=', 'LIKE', 'IN']
                if not any(op in condition.upper() for op in allowed_ops):
                    raise ValueError("Invalid condition")
                
                query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {condition}"
            else:
                query = f"SELECT COUNT(*) as count FROM {table_name}"
            
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "condition": condition,
                "row_count": result['count']
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get row count: {str(e)}"
            }
    
    async def get_recent_records(
        self,
        table_name: str,
        order_by: str = "id",
        limit: int = 10,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get recent records from a table."""
        try:
            # Validate inputs
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            
            if not order_by.replace('_', '').isalnum():
                raise ValueError("Invalid order_by column")
            
            limit = min(limit, 100)  # Cap at 100 records
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {table_name}
                ORDER BY {order_by} DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "order_by": order_by,
                "limit": limit,
                "row_count": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get recent records: {str(e)}"
            }
    
    async def search_records(
        self,
        table_name: str,
        search_column: str,
        search_term: str,
        limit: int = 50,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Search records in a table."""
        try:
            # Validate inputs
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            
            if not search_column.replace('_', '').isalnum():
                raise ValueError("Invalid search column")
            
            limit = min(limit, 100)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM {table_name}
                WHERE {search_column} LIKE ?
                LIMIT ?
            """
            
            cursor.execute(query, (f"%{search_term}%", limit))
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "search_column": search_column,
                "search_term": search_term,
                "row_count": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    async def get_statistics(
        self,
        table_name: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get basic statistics for a table."""
        try:
            # Validate table name
            if not table_name.replace('_', '').isalnum():
                raise ValueError("Invalid table name")
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as total_rows FROM {table_name}")
            total_rows = cursor.fetchone()['total_rows']
            
            # Get table size (approximate)
            cursor.execute("""
                SELECT page_count * page_size as size_bytes
                FROM pragma_page_count, pragma_page_size
            """)
            size_info = cursor.fetchone()
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "total_rows": total_rows,
                "column_count": len(columns),
                "approximate_size_bytes": size_info['size_bytes'] if size_info else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get statistics: {str(e)}"
            }
    
    @property
    def name(self) -> str:
        """Return the server name."""
        return "sql_lite"
    
    @property
    def supported_operations(self) -> List[str]:
        """Return list of supported operations."""
        return [
            "execute_query",
            "get_tables",
            "get_schema",
            "get_row_count", 
            "get_recent_records",
            "search_records",
            "get_statistics"
        ]
    
    def get_available_queries(self) -> List[Dict[str, str]]:
        """Get list of available predefined queries."""
        return [
            {
                "name": query_name,
                "description": query.strip().split('\n')[0].strip(),
                "parameters": query.count('?')
            }
            for query_name, query in self.PREDEFINED_QUERIES.items()
        ]