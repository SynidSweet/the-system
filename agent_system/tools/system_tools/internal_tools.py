"""
Internal MCP tools for system introspection and management.

These tools provide agents with access to system information and capabilities.
"""

from typing import Dict, Any, List, Optional
import json
from ..base_tool import SystemMCPTool
from pydantic import BaseModel, Field
from typing import Dict, Any

# Temporary compatibility model
class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None
from agent_system.config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()


class ListAgentsTool(SystemMCPTool):
    """Query available agent configurations"""
    
    def __init__(self) -> None:
        super().__init__(
            name="list_agents",
            description="Query available agent configurations in the system",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "deprecated", "testing", "all"],
                        "description": "Filter agents by status",
                        "default": "active"
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "Include full agent configuration details",
                        "default": False
                    }
                }
            }
        )
        self.permissions = ["database_read"]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        status_filter = kwargs.get("status", "active")
        include_details = kwargs.get("include_details", False)
        
        try:
            if status_filter == "all":
                agents = await database.agents.get_all_active()  # Will expand this method
            else:
                agents = await database.agents.get_all_active()
            
            if include_details:
                result = [agent.model_dump() for agent in agents]
            else:
                result = [
                    {
                        "name": agent.name,
                        "id": agent.id,
                        "status": agent.status,
                        "description": agent.instruction[:100] + "..." if len(agent.instruction) > 100 else agent.instruction
                    }
                    for agent in agents
                ]
            
            return MCPToolResult(
                success=True,
                result=result,
                metadata={
                    "tool_name": "list_agents",
                    "count": len(result),
                    "status_filter": status_filter
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to list agents: {str(e)}"
            )


class ListDocumentsTool(SystemMCPTool):
    """Query available context documents"""
    
    def __init__(self) -> None:
        super().__init__(
            name="list_documents",
            description="Query available context documents in the system",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter documents by category",
                        "enum": ["system", "process", "reference", "guide", "all"],
                        "default": "all"
                    },
                    "search": {
                        "type": "string",
                        "description": "Search documents by name or title"
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Include document content in results",
                        "default": False
                    }
                }
            }
        )
        self.permissions = ["database_read"]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        category = kwargs.get("category", "all")
        search = kwargs.get("search")
        include_content = kwargs.get("include_content", False)
        
        try:
            # For now, get all documents - would implement filtering in a real system
            query = "SELECT * FROM context_documents ORDER BY name"
            results = await database.db_manager.execute_query(query)
            
            documents = []
            for row in results:
                doc_data = {
                    "id": row["id"],
                    "name": row["name"],
                    "title": row["title"],
                    "category": row["category"],
                    "format": row["format"],
                    "version": row["version"]
                }
                
                if include_content:
                    doc_data["content"] = row["content"]
                
                # Apply filters
                if category != "all" and row["category"] != category:
                    continue
                    
                if search and search.lower() not in row["name"].lower() and search.lower() not in row["title"].lower():
                    continue
                
                documents.append(doc_data)
            
            return MCPToolResult(
                success=True,
                result=documents,
                metadata={
                    "tool_name": "list_documents",
                    "count": len(documents),
                    "category_filter": category
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to list documents: {str(e)}"
            )


class ListOptionalToolsTool(SystemMCPTool):
    """Query tools registry"""
    
    def __init__(self) -> None:
        super().__init__(
            name="list_optional_tools",
            description="Query the tools registry for available optional tools",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter tools by category",
                        "enum": ["core", "system", "custom", "external", "all"],
                        "default": "all"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "deprecated", "testing", "all"],
                        "description": "Filter tools by status",
                        "default": "active"
                    },
                    "include_config": {
                        "type": "boolean",
                        "description": "Include tool configuration details",
                        "default": False
                    }
                }
            }
        )
        self.permissions = ["database_read"]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        category = kwargs.get("category", "all")
        status_filter = kwargs.get("status", "active")
        include_config = kwargs.get("include_config", False)
        
        try:
            query = "SELECT * FROM tools ORDER BY category, name"
            results = await database.db_manager.execute_query(query)
            
            tools = []
            for row in results:
                # Apply filters
                if category != "all" and row["category"] != category:
                    continue
                if status_filter != "all" and row["status"] != status_filter:
                    continue
                
                tool_data = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "category": row["category"],
                    "version": row["version"],
                    "status": row["status"]
                }
                
                if include_config:
                    tool_data["implementation"] = json.loads(row["implementation"]) if row["implementation"] else {}
                    tool_data["parameters"] = json.loads(row["parameters"]) if row["parameters"] else {}
                    tool_data["permissions"] = json.loads(row["permissions"]) if row["permissions"] else []
                
                tools.append(tool_data)
            
            return MCPToolResult(
                success=True,
                result=tools,
                metadata={
                    "tool_name": "list_optional_tools",
                    "count": len(tools),
                    "category_filter": category,
                    "status_filter": status_filter
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to list tools: {str(e)}"
            )


class QueryDatabaseTool(SystemMCPTool):
    """Direct SQLite database queries (read-only for most agents)"""
    
    def __init__(self) -> None:
        super().__init__(
            name="query_database",
            description="Execute read-only database queries for system introspection",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only for safety)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return",
                        "default": 100,
                        "maximum": 1000
                    }
                },
                "required": ["query"]
            }
        )
        self.permissions = ["database_read"]
    
    def _is_query_safe(self, query: str) -> bool:
        """Ensure query is read-only"""
        query_lower = query.lower().strip()
        
        # Only allow SELECT statements
        if not query_lower.startswith("select"):
            return False
        
        # Block dangerous operations
        dangerous_keywords = [
            "insert", "update", "delete", "drop", "create", "alter", 
            "truncate", "exec", "execute", "pragma"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                return False
        
        return True
    
    async def execute(self, **kwargs) -> MCPToolResult:
        query = kwargs.get("query")
        limit = kwargs.get("limit", 100)
        
        if not self._is_query_safe(query):
            return MCPToolResult(
                success=False,
                error_message="Only SELECT queries are allowed for safety"
            )
        
        try:
            # Add LIMIT if not present
            if "limit" not in query.lower():
                query += f" LIMIT {limit}"
            
            results = await database.db_manager.execute_query(query)
            
            return MCPToolResult(
                success=True,
                result=results,
                metadata={
                    "tool_name": "query_database",
                    "row_count": len(results),
                    "query": query
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Database query failed: {str(e)}"
            )


def register_internal_tools(registry):
    """Register all internal MCP tools with the registry"""
    internal_tools = [
        ListAgentsTool(),
        ListDocumentsTool(),
        ListOptionalToolsTool(),
        QueryDatabaseTool()
    ]
    
    for tool in internal_tools:
        registry.register_tool(tool, "system")
    
    return internal_tools