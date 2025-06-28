"""Database-driven permission management system for tools and entities."""

import json
import time
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from ..database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class AgentPermissions:
    """Complete permissions for an agent including entity access and tools."""
    entity_access: Dict[str, List[str]]  # {"agent": ["read"], "task": ["read", "write"]}
    tools: List[str]  # List of available tool names
    tool_permissions: Dict[str, Dict[str, Any]]  # Tool-specific permissions


@dataclass
class ToolAssignment:
    """Tool assignment request with justification and constraints."""
    tool_name: str
    assignment_reason: str
    duration_hours: Optional[int] = None
    specific_permissions: Optional[Dict[str, Any]] = None


class DatabasePermissionManager:
    """Manages tool permissions and assignments using database backend."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._permission_cache = {}  # Cache for performance
        self._cache_ttl = 300  # 5 minutes
        
    async def get_agent_permissions(self, agent_type: str, task_id: int = None) -> AgentPermissions:
        """Get complete permissions for agent including task-specific tools."""
        # Check cache first
        cache_key = f"{agent_type}:{task_id}"
        if cache_key in self._permission_cache:
            cached_data, cached_time = self._permission_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_data
        
        # Get base permissions
        base_query = """
            SELECT entity_permissions, base_tools 
            FROM agent_base_permissions 
            WHERE agent_type = ?
        """
        result = await self.db.agents.execute_query(base_query, [agent_type])
        
        if not result:
            raise ValueError(f"No base permissions found for agent type: {agent_type}")
        
        base_result = result[0]
        entity_permissions = json.loads(base_result['entity_permissions'])
        base_tools = json.loads(base_result['base_tools'])
        
        # Get task-specific tool assignments
        task_tools = []
        tool_permissions = {}
        
        if task_id:
            task_query = """
                SELECT tool_name, tool_permissions 
                FROM task_tool_assignments 
                WHERE task_id = ? 
                AND is_active = 1 
                AND (expires_at IS NULL OR expires_at > datetime('now'))
            """
            task_results = await self.db.agents.execute_query(task_query, [task_id])
            
            for row in task_results:
                task_tools.append(row['tool_name'])
                if row['tool_permissions']:
                    tool_permissions[row['tool_name']] = json.loads(row['tool_permissions'])
        
        permissions = AgentPermissions(
            entity_access=entity_permissions,
            tools=base_tools + task_tools,
            tool_permissions=tool_permissions
        )
        
        # Cache the result
        self._permission_cache[cache_key] = (permissions, time.time())
        
        return permissions
    
    async def assign_tool_to_task(self, task_id: int, tool_assignment: ToolAssignment, 
                                 assigned_by: int) -> bool:
        """Assign tool to specific task with optional expiration."""
        # Verify tool exists
        tool_query = "SELECT tool_name, security_level FROM available_tools WHERE tool_name = ? AND is_active = 1"
        tool_result = await self.db.agents.execute_query(tool_query, [tool_assignment.tool_name])
        
        if not tool_result:
            raise ValueError(f"Tool '{tool_assignment.tool_name}' not found or inactive")
        
        expires_at = None
        if tool_assignment.duration_hours:
            expires_at = datetime.now() + timedelta(hours=tool_assignment.duration_hours)
            expires_at = expires_at.isoformat()
        
        tool_permissions_json = None
        if tool_assignment.specific_permissions:
            tool_permissions_json = json.dumps(tool_assignment.specific_permissions)
        
        # Check if assignment already exists
        check_query = """
            SELECT id FROM task_tool_assignments 
            WHERE task_id = ? AND tool_name = ? AND is_active = 1
        """
        existing = await self.db.agents.execute_query(check_query, [task_id, tool_assignment.tool_name])
        
        if existing:
            # Update existing assignment
            update_query = """
                UPDATE task_tool_assignments 
                SET expires_at = ?, assignment_reason = ?, tool_permissions = ?,
                    assigned_at = CURRENT_TIMESTAMP
                WHERE task_id = ? AND tool_name = ?
            """
            await self.db.agents.execute_query(update_query, [
                expires_at, tool_assignment.assignment_reason, tool_permissions_json,
                task_id, tool_assignment.tool_name
            ])
        else:
            # Create new assignment
            insert_query = """
                INSERT INTO task_tool_assignments 
                (task_id, tool_name, tool_permissions, assigned_by_agent_id, expires_at, assignment_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            await self.db.agents.execute_query(insert_query, [
                task_id, tool_assignment.tool_name, tool_permissions_json,
                assigned_by, expires_at, tool_assignment.assignment_reason
            ])
        
        # Clear cache for this task
        self._clear_cache_for_task(task_id)
        
        # Log tool assignment event
        await self._log_tool_assignment(task_id, tool_assignment, assigned_by)
        
        logger.info(f"Assigned tool '{tool_assignment.tool_name}' to task {task_id}")
        return True
    
    async def check_permission(self, agent_type: str, task_id: int, 
                              operation: str, entity_type: str) -> bool:
        """Check if agent has permission for specific operation on entity type."""
        permissions = await self.get_agent_permissions(agent_type, task_id)
        
        # Check entity permissions
        if entity_type in permissions.entity_access:
            return operation in permissions.entity_access[entity_type]
        
        # Check for wildcard permissions
        if "all" in permissions.entity_access:
            return operation in permissions.entity_access["all"]
        
        return False
    
    async def check_tool_access(self, agent_type: str, task_id: int, tool_name: str) -> bool:
        """Check if agent has access to specific tool."""
        permissions = await self.get_agent_permissions(agent_type, task_id)
        return tool_name in permissions.tools
    
    async def log_tool_usage(self, task_id: int, agent_type: str, tool_name: str, 
                           operation: str, success: bool, execution_time_ms: int,
                           parameters_hash: str = None, result_summary: str = None,
                           error_message: str = None):
        """Log tool usage for optimization analysis."""
        query = """
            INSERT INTO tool_usage_events 
            (task_id, agent_type, tool_name, operation, success, execution_time_ms, 
             parameters_hash, result_summary, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.db.agents.execute_query(query, [
            task_id, agent_type, tool_name, operation, 
            1 if success else 0, execution_time_ms, 
            parameters_hash, result_summary, error_message
        ])
    
    async def revoke_tool_from_task(self, task_id: int, tool_name: str) -> bool:
        """Revoke tool access from task."""
        query = """
            UPDATE task_tool_assignments 
            SET is_active = 0 
            WHERE task_id = ? AND tool_name = ?
        """
        
        await self.db.agents.execute_query(query, [task_id, tool_name])
        
        # Clear cache
        self._clear_cache_for_task(task_id)
        
        logger.info(f"Revoked tool '{tool_name}' from task {task_id}")
        return True
    
    async def cleanup_expired_assignments(self):
        """Remove expired tool assignments."""
        query = """
            UPDATE task_tool_assignments 
            SET is_active = 0 
            WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')
            AND is_active = 1
        """
        result = await self.db.agents.execute_query(query)
        
        # Clear entire cache after cleanup
        self._permission_cache.clear()
        
        logger.info("Cleaned up expired tool assignments")
    
    async def get_tool_usage_stats(self, tool_name: str = None, 
                                  agent_type: str = None, 
                                  days: int = 7) -> List[Dict[str, Any]]:
        """Get tool usage statistics for optimization."""
        conditions = ["used_at > datetime('now', ?  || ' days')"]
        params = [-days]
        
        if tool_name:
            conditions.append("tool_name = ?")
            params.append(tool_name)
            
        if agent_type:
            conditions.append("agent_type = ?")
            params.append(agent_type)
        
        query = f"""
            SELECT 
                tool_name,
                agent_type,
                COUNT(*) as usage_count,
                AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(execution_time_ms) as avg_execution_time,
                MIN(used_at) as first_used,
                MAX(used_at) as last_used
            FROM tool_usage_events
            WHERE {' AND '.join(conditions)}
            GROUP BY tool_name, agent_type
            ORDER BY usage_count DESC
        """
        
        return await self.db.agents.execute_query(query, params)
    
    async def get_active_tool_assignments(self, task_id: int = None) -> List[Dict[str, Any]]:
        """Get currently active tool assignments."""
        if task_id:
            query = """
                SELECT * FROM active_tool_assignments
                WHERE task_id = ?
                ORDER BY assigned_at DESC
            """
            params = [task_id]
        else:
            query = """
                SELECT * FROM active_tool_assignments
                ORDER BY assigned_at DESC
            """
            params = []
        
        return await self.db.agents.execute_query(query, params)
    
    async def _log_tool_assignment(self, task_id: int, tool_assignment: ToolAssignment, 
                                  assigned_by: int):
        """Log tool assignment as event."""
        # This would integrate with event system
        logger.info(f"Tool assignment logged: {tool_assignment.tool_name} to task {task_id} by {assigned_by}")
    
    def _clear_cache_for_task(self, task_id: int):
        """Clear permission cache entries for a specific task."""
        keys_to_remove = [k for k in self._permission_cache.keys() if k.endswith(f":{task_id}")]
        for key in keys_to_remove:
            del self._permission_cache[key]
    
    def hash_parameters(self, parameters: Dict[str, Any]) -> str:
        """Create hash of parameters for tracking patterns."""
        # Sort keys for consistent hashing
        sorted_params = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()


# Singleton instance management
_permission_manager: Optional[DatabasePermissionManager] = None


def get_permission_manager(db_manager: DatabaseManager) -> DatabasePermissionManager:
    """Get or create the permission manager instance."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = DatabasePermissionManager(db_manager)
    return _permission_manager