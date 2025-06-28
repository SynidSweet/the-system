"""
Universal Agent Runtime - New implementation that works with the runtime engine.

This replaces the old message-based agent execution with a process-based approach.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent_system.core.entities import (
    TaskEntity, AgentEntity, ToolEntity, ContextEntity,
    TaskState, EntityManager
)
from agent_system.core.events.models import Event

# Legacy model imports that still need to be implemented
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

# Temporary compatibility models - these should be migrated properly
class MessageType(str, Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"

class Message(BaseModel):
    id: Optional[int] = None
    task_id: int
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_message_id: Optional[int] = None
    timestamp: Optional[float] = None
    token_count: Optional[int] = None
    execution_time_ms: Optional[int] = None

class MCPToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None

class MCPToolResult(BaseModel):
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[int] = None

class AgentExecutionContext(BaseModel):
    task: TaskEntity
    agent: AgentEntity
    context_documents: List[ContextEntity] = Field(default_factory=list)
    available_tools: List[ToolEntity] = Field(default_factory=list)
    message_history: List[Message] = Field(default_factory=list)
    recursion_depth: int = 0

class AgentExecutionResult(BaseModel):
    status: TaskState
    result: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    spawned_tasks: List[int] = Field(default_factory=list)
    tool_calls_made: int = 0
    execution_time_seconds: float = 0

# Type aliases for backward compatibility
Task = TaskEntity
Agent = AgentEntity
Tool = ToolEntity
ContextDocument = ContextEntity
TaskStatus = TaskState
from agent_system.config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()
from .ai_models import ai_model_manager
from .websocket_messages import WebSocketMessage, MessageBuilder
from .websocket_messages import MessageType as WSMessageType
from .runtime.runtime_integration import get_runtime_integration
from .runtime.state_machine import TaskState
from .events.event_manager import EventManager
from .events.event_types import EventType, EntityType, EventOutcome
from tools.base_tool import tool_registry
from config.settings import settings
from config.model_config import AGENT_MODEL_PREFERENCES, ModelSelector


class UniversalAgentRuntime:
    """
    Universal Agent that executes within the new runtime engine.
    
    Key differences from old agent:
    - Tool calls trigger processes instead of direct execution
    - State management through runtime engine
    - Event-driven execution model
    """
    
    def __init__(self, task_id: int, event_manager: EventManager):
        self.task_id = task_id
        self.event_manager = event_manager
        self.execution_context: Optional[AgentExecutionContext] = None
        self.start_time: Optional[float] = None
        self.tool_calls_made = 0
        self.messages_logged = 0
        self.tree_id: Optional[int] = None
        self.runtime = get_runtime_integration()
    
    async def initialize(self) -> bool:
        """Initialize the agent with task context"""
        try:
            # Load task from database
            task = await database.tasks.get_by_id(self.task_id)
            if not task:
                raise ValueError(f"Task {self.task_id} not found")
            
            self.tree_id = task.tree_id
            
            # Load agent configuration
            agent = await database.agents.get_by_id(task.agent_id)
            if not agent:
                # Try to get agent by name if ID lookup fails
                agent_name = task.metadata.get('assigned_agent') if task.metadata else None
                if agent_name:
                    agent = await database.agents.get_by_name(agent_name)
                
                if not agent:
                    raise ValueError(f"Agent for task {self.task_id} not found")
            
            # Load context documents
            context_documents = []
            if agent.context_documents:
                context_documents = await database.context_documents.get_by_names(
                    agent.context_documents
                )
            
            # Add any additional context from task
            if task.metadata and task.metadata.get('additional_context'):
                additional_context = await database.context_documents.get_by_names(
                    task.metadata['additional_context']
                )
                context_documents.extend(additional_context)
            
            # Load available tools
            available_tools = []
            if agent.available_tools:
                available_tools = await database.tools.get_by_names(
                    agent.available_tools
                )
            
            # Add any additional tools from task
            if task.metadata and task.metadata.get('additional_tools'):
                additional_tools = await database.tools.get_by_names(
                    task.metadata['additional_tools']
                )
                available_tools.extend(additional_tools)
            
            # Add MCP tools based on permissions
            from agent_system.tools.mcp_servers.startup import get_tool_system_manager
            tool_system = get_tool_system_manager()
            if tool_system:
                # Get agent type from task metadata or agent name
                agent_type = task.metadata.get("agent_type", agent.name)
                mcp_tools = await tool_system.get_agent_tools(agent_type, self.task_id)
                
                # Create tool objects for MCP tools
                for tool_name in mcp_tools:
                    from agent_system.core.models import Tool
                    # Create pseudo-tool objects for MCP servers
                    mcp_tool = Tool(
                        id=0,
                        name=tool_name,
                        description=f"MCP Server: {tool_name} - Access to {tool_name} operations",
                        function_name=tool_name,
                        parameters={},
                        returns={}
                    )
                    available_tools.append(mcp_tool)
            
            # Load message history
            message_history = await database.messages.get_by_task_id(self.task_id)
            
            # Create execution context
            self.execution_context = AgentExecutionContext(
                task=task,
                agent=agent,
                context_documents=context_documents,
                available_tools=available_tools,
                message_history=message_history,
                recursion_depth=self._calculate_recursion_depth(task)
            )
            
            return True
            
        except Exception as e:
            await self._log_message(
                MessageType.ERROR,
                f"Agent initialization failed: {str(e)}",
                {"initialization_error": True, "exception": str(e)}
            )
            return False
    
    async def execute(self) -> AgentExecutionResult:
        """Execute the agent's task"""
        self.start_time = time.time()
        
        try:
            # Log execution start
            await self.event_manager.log_event(
                EventType.TASK_STARTED,
                EntityType.TASK,
                self.task_id,
                task_instruction=self.execution_context.task.instruction,
                agent_name=self.execution_context.agent.name
            )
            
            # Prepare AI prompt
            prompt = self._build_prompt()
            
            # Get AI response
            response = await ai_model_manager.get_response(
                prompt,
                model_config=self.execution_context.agent.model_config
            )
            
            # Process tool calls
            tool_results = []
            if response.tool_calls:
                tool_results = await self._process_tool_calls(response.tool_calls)
            
            # Log agent response
            await self._log_message(
                MessageType.AGENT_RESPONSE,
                response.content or "No response content",
                {"thinking": True}
            )
            
            # Determine result
            execution_time = time.time() - self.start_time
            
            # Check if task is complete
            task_complete = self._check_task_completion(response, tool_results)
            
            result = AgentExecutionResult(
                success=True,
                result=self._extract_result(response, tool_results),
                messages_logged=self.messages_logged,
                tool_calls_made=self.tool_calls_made,
                execution_time=execution_time,
                task_complete=task_complete
            )
            
            # Log completion
            await self.event_manager.log_event(
                EventType.TASK_COMPLETED,
                EntityType.TASK,
                self.task_id,
                result=result.result,
                execution_time=execution_time,
                outcome=EventOutcome.SUCCESS
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - self.start_time if self.start_time else 0
            
            await self._log_message(
                MessageType.ERROR,
                f"Task execution failed: {str(e)}",
                {"exception": str(e)}
            )
            
            await self.event_manager.log_event(
                EventType.TASK_FAILED,
                EntityType.TASK,
                self.task_id,
                error=str(e),
                execution_time=execution_time,
                outcome=EventOutcome.FAILURE
            )
            
            return AgentExecutionResult(
                success=False,
                error_message=str(e),
                messages_logged=self.messages_logged,
                tool_calls_made=self.tool_calls_made,
                execution_time=execution_time,
                task_complete=False
            )
    
    async def _process_tool_calls(self, tool_calls: List[MCPToolCall]) -> List[MCPToolResult]:
        """Process tool calls through the runtime integration"""
        results = []
        
        for tool_call in tool_calls:
            self.tool_calls_made += 1
            
            # Log tool call
            await self._log_message(
                MessageType.TOOL_CALL,
                f"Calling tool: {tool_call.tool_name}",
                {
                    "tool_name": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "call_id": tool_call.call_id
                }
            )
            
            # Process through runtime integration
            try:
                if self.runtime:
                    # Use runtime to handle tool call (may trigger process)
                    result = await self.runtime.handle_tool_call(
                        self.task_id,
                        tool_call.tool_name,
                        tool_call.parameters
                    )
                    
                    tool_result = MCPToolResult(
                        success=result.get("status") in ["process_executed", "tool_executed"],
                        result=result,
                        metadata={"runtime_result": True}
                    )
                else:
                    # Fallback to direct tool execution
                    tool_result = await tool_registry.execute_tool(tool_call)
                
                results.append(tool_result)
                
                # Log tool result
                await self._log_message(
                    MessageType.TOOL_RESPONSE,
                    f"Tool result: {tool_result.result if tool_result.success else tool_result.error_message}",
                    {
                        "tool_name": tool_call.tool_name,
                        "success": tool_result.success,
                        "metadata": tool_result.metadata,
                        "call_id": tool_call.call_id
                    }
                )
                
            except Exception as e:
                error_result = MCPToolResult(
                    success=False,
                    error_message=f"Tool execution failed: {str(e)}",
                    metadata={"exception": str(e), "tool_name": tool_call.tool_name}
                )
                results.append(error_result)
                
                await self._log_message(
                    MessageType.ERROR,
                    f"Tool execution error: {str(e)}",
                    {"tool_name": tool_call.tool_name, "exception": str(e)}
                )
        
        return results
    
    def _build_prompt(self) -> str:
        """Build the prompt for the AI model"""
        context = self.execution_context
        
        # Base prompt
        prompt = f"""You are {context.agent.name}.

{context.agent.instruction}

Current Task: {context.task.instruction}

"""
        
        # Add context documents
        if context.context_documents:
            prompt += "Available Context:\n"
            for doc in context.context_documents:
                prompt += f"\n{doc.title}:\n{doc.content}\n"
            prompt += "\n"
        
        # Add available tools
        if context.available_tools:
            prompt += "Available Tools:\n"
            for tool in context.available_tools:
                prompt += f"- {tool.name}: {tool.description}\n"
            prompt += "\n"
        
        # Add conversation history
        if context.message_history:
            prompt += "Conversation History:\n"
            for msg in context.message_history[-10:]:  # Last 10 messages
                if msg.message_type == MessageType.AGENT_RESPONSE:
                    prompt += f"Assistant: {msg.content}\n"
                elif msg.message_type == MessageType.TOOL_CALL:
                    prompt += f"Tool Call: {msg.metadata.get('tool_name', 'unknown')}\n"
                elif msg.message_type == MessageType.TOOL_RESPONSE:
                    prompt += f"Tool Result: {msg.content}\n"
            prompt += "\n"
        
        # Add recursion depth warning
        if context.recursion_depth > 5:
            prompt += f"\nWARNING: You are at recursion depth {context.recursion_depth}. Consider completing soon to avoid infinite loops.\n"
        
        return prompt
    
    def _calculate_recursion_depth(self, task: Task) -> int:
        """Calculate the recursion depth of the current task"""
        depth = 0
        current_task = task
        
        while current_task.parent_task_id:
            depth += 1
            if depth > 10:  # Safety limit
                break
            # In a real implementation, would load parent task
            break
        
        return depth
    
    def _check_task_completion(self, response: Any, tool_results: List[MCPToolResult]) -> bool:
        """Check if the task is complete based on response and tool results"""
        # Check if end_task was called
        for result in tool_results:
            if result.metadata and result.metadata.get("tool_name") == "end_task":
                return True
        
        # Check for completion indicators in response
        if response.content:
            completion_phrases = [
                "task is complete",
                "task completed",
                "finished the task",
                "successfully completed"
            ]
            content_lower = response.content.lower()
            if any(phrase in content_lower for phrase in completion_phrases):
                return True
        
        return False
    
    def _extract_result(self, response: Any, tool_results: List[MCPToolResult]) -> Dict[str, Any]:
        """Extract the result from response and tool results"""
        result = {
            "response": response.content,
            "tool_results": [
                {
                    "tool": r.metadata.get("tool_name") if r.metadata else "unknown",
                    "success": r.success,
                    "result": r.result if r.success else r.error_message
                }
                for r in tool_results
            ]
        }
        
        # Check for end_task result
        for r in tool_results:
            if r.metadata and r.metadata.get("tool_name") == "end_task" and r.success:
                if isinstance(r.result, dict) and "result" in r.result:
                    result["final_result"] = r.result["result"]
        
        return result
    
    async def _log_message(
        self,
        message_type: MessageType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a message to the database"""
        self.messages_logged += 1
        
        message = Message(
            task_id=self.task_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        await database.messages.create(message)
    
    async def _broadcast_message(self, ws_message: WebSocketMessage):
        """Broadcast a message through websocket"""
        # This would be implemented to send through the websocket manager
        pass