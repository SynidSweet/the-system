"""
Agent management tools for creating and modifying agents.
"""

from typing import Dict, Any, List, Optional
from core.models import Agent, Tool, MCPToolResult
from core.database_manager import database
from tools.base_tool import BaseMCPTool, tool_registry


class CreateAgentTool(BaseMCPTool):
    """Tool for creating new agents in the system"""
    
    def __init__(self):
        super().__init__(
            name="create_agent",
            description="Create a new specialized agent in the system"
        )
        self.category = "agent_management"
    
    async def execute(self, **kwargs) -> MCPToolResult:
        """Create a new agent with the specified configuration"""
        
        # Extract required parameters
        agent_name = kwargs.get("name")
        instruction = kwargs.get("instruction")
        
        if not agent_name or not instruction:
            return MCPToolResult(
                success=False,
                error_message="Missing required parameters: name and instruction"
            )
        
        # Validate agent name format
        if not agent_name.islower() or ' ' in agent_name:
            return {
                "success": False,
                "error": "Agent name must be lowercase with underscores (e.g., my_agent)"
            }
        
        # Check if agent already exists
        existing = await database.agents.get_by_name(agent_name)
        if existing:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' already exists"
            }
        
        # Create the agent
        try:
            agent = Agent(
                name=agent_name,
                instruction=instruction,
                system_prompt=parameters.get("system_prompt", "You are a specialized agent in a self-improving system."),
                context_documents=parameters.get("context_documents", []),
                available_tools=parameters.get("available_tools", ["end_task"]),
                permissions=parameters.get("permissions", {}),
                constraints=parameters.get("constraints", {}),
                llm_config=parameters.get("llm_config", {"model": "claude-3-sonnet-20240229"}),
                is_active=True
            )
            
            agent_id = await database.agents.create(agent)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "message": f"Successfully created agent '{agent_name}' with ID {agent_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create agent: {str(e)}"
            }


class ListAgentsTool(BaseMCPTool):
    """Tool for listing all agents in the system"""
    
    name = "list_agents"
    description = "List all available agents and their purposes"
    category = "agent_management"
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List all agents with their basic information"""
        
        try:
            agents = await database.agents.get_all_active()
            
            agent_list = []
            for agent in agents:
                agent_list.append({
                    "name": agent.name,
                    "id": agent.id,
                    "purpose": agent.instruction[:200] + "..." if len(agent.instruction) > 200 else agent.instruction,
                    "tools": agent.available_tools,
                    "context_docs": agent.context_documents
                })
            
            return {
                "success": True,
                "agents": agent_list,
                "total_count": len(agent_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list agents: {str(e)}"
            }


class TestAgentSelectionTool(BaseMCPTool):
    """Tool for testing if an agent would be selected for a given task"""
    
    name = "test_agent_selection"
    description = "Test which agent would be selected for a given instruction"
    category = "agent_management"
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Test agent selection logic"""
        
        instruction = parameters.get("instruction")
        if not instruction:
            return {
                "success": False,
                "error": "Missing required parameter: instruction"
            }
        
        try:
            # This would normally call the agent_selector logic
            # For now, we'll do a simple keyword match simulation
            agents = await database.agents.get_all_active()
            
            # Simple scoring based on instruction overlap
            scores = []
            for agent in agents:
                if agent.name == "agent_selector":
                    continue  # Skip the selector itself
                
                # Simple keyword matching (in production, this would use the actual selector logic)
                agent_keywords = set(agent.name.split('_') + agent.instruction.lower().split()[:20])
                instruction_keywords = set(instruction.lower().split())
                overlap = len(agent_keywords & instruction_keywords)
                
                scores.append({
                    "agent": agent.name,
                    "score": overlap,
                    "would_select": overlap > 2
                })
            
            # Sort by score
            scores.sort(key=lambda x: x["score"], reverse=True)
            
            selected = scores[0] if scores and scores[0]["would_select"] else None
            
            return {
                "success": True,
                "instruction": instruction,
                "selected_agent": selected["agent"] if selected else "agent_selector",
                "all_scores": scores[:5]  # Top 5 candidates
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to test agent selection: {str(e)}"
            }


# Register the tools
tool_registry.register_tool(CreateAgentTool(), "system")
tool_registry.register_tool(ListAgentsTool(), "system") 
tool_registry.register_tool(TestAgentSelectionTool(), "system")