import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import (
    Task, Agent, Message, ContextDocument, Tool, 
    TaskStatus, MessageType, AgentExecutionContext, 
    AgentExecutionResult, MCPToolCall, MCPToolResult
)
from .database_manager import database
from .ai_models import ai_model_manager
from .websocket_messages import WebSocketMessage, MessageBuilder
from .websocket_messages import MessageType as WSMessageType
from tools.base_tool import tool_registry
from config.settings import settings


class UniversalAgent:
    """
    Universal Agent Runtime - The core of the recursive agent system.
    
    Every agent instance is fundamentally identical:
    - Same core instruction set and MCP toolkit
    - Same communication protocols
    - Different task instructions, context, and available tools
    """
    
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.execution_context: Optional[AgentExecutionContext] = None
        self.start_time: Optional[float] = None
        self.tool_calls_made = 0
        self.messages_logged = 0
        self.spawned_tasks: List[int] = []
        self.task_manager = None  # Set by TaskManager
        self.tree_id: Optional[int] = None
    
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
                raise ValueError(f"Agent {task.agent_id} not found")
            
            # Load context documents
            context_documents = []
            if agent.context_documents:
                context_documents = await database.context_documents.get_by_names(
                    agent.context_documents
                )
            
            # Load available tools
            available_tools = []
            if agent.available_tools:
                available_tools = await database.tools.get_by_names(
                    agent.available_tools
                )
            
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
            # Update task status to running
            await database.tasks.update_status(self.task_id, TaskStatus.RUNNING)
            
            # Broadcast agent started
            await self._broadcast_message(
                MessageBuilder.agent_started(
                    self.task_id, 
                    self.tree_id,
                    self.execution_context.agent.name,
                    self.execution_context.task.instruction
                )
            )
            
            await self._log_message(
                MessageType.SYSTEM_EVENT,
                f"Starting task execution: {self.execution_context.task.instruction}",
                {"task_id": self.task_id, "agent_type": self.execution_context.agent.name}
            )
            
            
            # Build and execute conversation
            result = await self._execute_conversation()
            
            # Complete successfully
            return await self._complete_successfully(result)
            
        except Exception as e:
            return await self._complete_with_error(f"Execution failed: {str(e)}")
    
    async def _execute_conversation(self) -> str:
        """Execute the main conversation loop with the AI model"""
        
        # Build initial prompt
        prompt = await self._build_prompt()
        
        # Prepare conversation messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": self.execution_context.task.instruction}
        ]
        
        # Add message history
        for msg in self.execution_context.message_history:
            if msg.message_type == MessageType.AGENT_RESPONSE:
                messages.append({"role": "assistant", "content": msg.content})
            elif msg.message_type == MessageType.USER_INPUT:
                messages.append({"role": "user", "content": msg.content})
        
        # Get AI model provider
        ai_provider = await ai_model_manager.get_provider(
            self.execution_context.agent.llm_config
        )
        
        # Prepare available tools for the model
        tool_schemas = self._get_tool_schemas()
        
        # Main conversation loop
        max_iterations = 50  # Simple default limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Generate AI response
            response = await ai_provider.generate_response(
                messages=messages,
                tools=tool_schemas
            )
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            
            # Log the response
            await self._log_message(
                MessageType.AGENT_RESPONSE,
                content,
                {
                    "model": response.get("model"),
                    "usage": response.get("usage"),
                    "stop_reason": response.get("stop_reason"),
                    "tool_calls_count": len(tool_calls)
                }
            )
            
            # Add response to conversation
            messages.append({"role": "assistant", "content": content})
            
            # Process tool calls
            if tool_calls:
                tool_results = await self._process_tool_calls(tool_calls)
                
                # Add tool results to conversation
                for i, (tool_call, result) in enumerate(zip(tool_calls, tool_results)):
                    result_content = f"Tool '{tool_call.tool_name}' result: {result.result if result.success else result.error_message}"
                    messages.append({"role": "user", "content": result_content})
                
                # Check if any tool ended the task
                if any(result.metadata.get("action") == "complete_task" for result in tool_results):
                    break
            else:
                # No tool calls, conversation is complete
                break
        
        return content
    
    async def _build_prompt(self) -> str:
        """Build the complete system prompt for the agent"""
        
        base_prompt = f"""You are a universal agent in a recursive task-solving system. Your specific task is: {self.execution_context.task.instruction}

CORE PRINCIPLES:
1. Use think_out_loud() FREQUENTLY to log your reasoning, observations, and planning thoughts - this creates transparency and helps with debugging
2. Solve ONLY the specific task you've been given
3. Use available tools when you need to spawn other agents or modify the system
4. If the task is too complex, break it down using break_down_task()
5. If you need more context or tools, request them explicitly
6. Always end with end_task() indicating success or failure

THINKING AND TRANSPARENCY:
- Use think_out_loud() at key decision points to explain your reasoning
- Log observations about the task, system state, and potential approaches
- Document your planning process and any uncertainties
- Share reflections on what's working or not working
- This creates a valuable audit trail for system improvement

AVAILABLE TOOLS:
{self._format_available_tools()}

CONTEXT DOCUMENTS:
{self._format_context_documents()}

Agent Type: {self.execution_context.agent.name}
Task ID: {self.task_id}
Tree ID: {self.execution_context.task.tree_id}

Complete your assigned task efficiently and precisely."""
        
        return base_prompt
    
    def _format_available_tools(self) -> str:
        """Format available tools for the prompt"""
        if not self.execution_context.available_tools:
            return "No additional tools available."
        
        tools_text = []
        for tool in self.execution_context.available_tools:
            tools_text.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tools_text)
    
    def _format_context_documents(self) -> str:
        """Format context documents for the prompt"""
        if not self.execution_context.context_documents:
            return "No additional context documents."
        
        context_text = []
        for doc in self.execution_context.context_documents:
            context_text.append(f"\n=== {doc.title} ===\n{doc.content}")
        
        return "\n".join(context_text)
    
    def _get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas for AI model"""
        schemas = []
        
        # Get core tools (always available)
        agent_permissions = ["core_toolkit"]
        if self.execution_context.agent.permissions.shell_access:
            agent_permissions.append("shell_access")
        if self.execution_context.agent.permissions.git_operations:
            agent_permissions.append("git_operations")
        if self.execution_context.agent.permissions.database_write:
            agent_permissions.extend(["database_read", "database_write"])
        else:
            agent_permissions.append("database_read")
        
        # Get available tools from registry
        available_tools = tool_registry.get_available_tools(agent_permissions)
        schemas.extend(tool_registry.get_tool_schemas(agent_permissions))
        
        return schemas
    
    async def _process_tool_calls(self, tool_calls: List[MCPToolCall]) -> List[MCPToolResult]:
        """Process all tool calls"""
        results = []
        
        for tool_call in tool_calls:
            self.tool_calls_made += 1
            
            # Broadcast tool call
            await self._broadcast_message(
                MessageBuilder.tool_call(
                    self.task_id,
                    self.tree_id,
                    self.execution_context.agent.name,
                    tool_call.tool_name,
                    tool_call.parameters
                )
            )
            
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
            
            # Execute tool
            try:
                result = await self._execute_tool_with_context(tool_call)
                results.append(result)
                
                # Broadcast tool result
                await self._broadcast_message(
                    MessageBuilder.tool_result(
                        self.task_id,
                        self.tree_id,
                        self.execution_context.agent.name,
                        tool_call.tool_name,
                        result.result if result.success else result.error_message,
                        result.success
                    )
                )
                
                # Log tool result
                await self._log_message(
                    MessageType.TOOL_RESPONSE,
                    f"Tool result: {result.result if result.success else result.error_message}",
                    {
                        "tool_name": tool_call.tool_name,
                        "success": result.success,
                        "metadata": result.metadata,
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
    
    async def _execute_tool_with_context(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Execute a tool call with agent context"""
        
        # Handle core tools that need agent context
        if tool_call.tool_name in ["start_subtask", "break_down_task", "end_task", "request_context", "request_tools"]:
            # Add task context to parameters
            tool_call.parameters["_current_task_id"] = self.task_id
            return await self._handle_core_tool(tool_call)
        
        # Regular tool execution
        return await tool_registry.execute_tool(tool_call)
    
    async def _handle_core_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Handle core tools that need special agent context"""
        
        # Check if the tool is registered in the tool registry
        tool = tool_registry.get_tool(tool_call.tool_name)
        if tool:
            # Use the registered implementation
            return await tool_registry.execute_tool(tool_call)
        
        # Fallback to hardcoded implementations for backward compatibility
        if tool_call.tool_name == "start_subtask":
            return await self._handle_start_subtask(tool_call)
        elif tool_call.tool_name == "break_down_task":
            return await self._handle_break_down_task(tool_call)
        elif tool_call.tool_name == "end_task":
            return await self._handle_end_task(tool_call)
        
        return MCPToolResult(
            success=False,
            error_message=f"Core tool '{tool_call.tool_name}' not found"
        )
    
    async def _handle_start_subtask(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Handle subtask creation"""
        params = tool_call.parameters
        task_instruction = params.get("task_instruction")
        agent_type = params.get("agent_type")
        priority = params.get("priority", 0)
        max_execution_time = params.get("max_execution_time", 300)
        
        try:
            # Get agent configuration
            agent = await database.agents.get_by_name(agent_type)
            if not agent:
                return MCPToolResult(
                    success=False,
                    error_message=f"Agent type '{agent_type}' not found"
                )
            
            # Create subtask
            subtask = Task(
                parent_task_id=self.task_id,
                tree_id=self.execution_context.task.tree_id,
                agent_id=agent.id,
                instruction=task_instruction,
                priority=priority,
                max_execution_time=max_execution_time
            )
            
            subtask_id = await database.tasks.create(subtask)
            self.spawned_tasks.append(subtask_id)
            
            return MCPToolResult(
                success=True,
                result=f"Subtask {subtask_id} created for agent '{agent_type}'",
                metadata={
                    "subtask_id": subtask_id,
                    "agent_type": agent_type,
                    "action": "subtask_created"
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to create subtask: {str(e)}"
            )
    
    async def _handle_break_down_task(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Handle task breakdown"""
        params = tool_call.parameters
        reasoning = params.get("reasoning")
        
        try:
            # Create a breakdown subtask with task_breakdown agent
            breakdown_agent = await database.agents.get_by_name("task_breakdown")
            if not breakdown_agent:
                return MCPToolResult(
                    success=False,
                    error_message="Task breakdown agent not found"
                )
            
            breakdown_instruction = f"Break down this task: {self.execution_context.task.instruction}\n\nReasoning: {reasoning}"
            
            subtask = Task(
                parent_task_id=self.task_id,
                tree_id=self.execution_context.task.tree_id,
                agent_id=breakdown_agent.id,
                instruction=breakdown_instruction,
                priority=5  # High priority for breakdown
            )
            
            subtask_id = await database.tasks.create(subtask)
            self.spawned_tasks.append(subtask_id)
            
            # Update current task to wait for subtasks
            await database.tasks.update_status(
                self.task_id, 
                TaskStatus.WAITING_SUBTASKS
            )
            
            return MCPToolResult(
                success=True,
                result=f"Task breakdown initiated (subtask {subtask_id})",
                metadata={
                    "subtask_id": subtask_id,
                    "reasoning": reasoning,
                    "action": "breakdown_initiated"
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to initiate breakdown: {str(e)}"
            )
    
    async def _handle_end_task(self, tool_call: MCPToolCall) -> MCPToolResult:
        """Handle task completion"""
        params = tool_call.parameters
        status = params.get("status")
        result = params.get("result")
        summary = params.get("summary", "")
        
        try:
            task_status = TaskStatus.COMPLETE if status == "success" else TaskStatus.FAILED
            
            # Update task in database
            await database.tasks.update_status(
                self.task_id,
                task_status,
                result=result,
                summary=summary
            )
            
            # TODO: Trigger evaluator and documentation agents
            
            return MCPToolResult(
                success=True,
                result=f"Task completed with status: {status}",
                metadata={
                    "task_status": task_status.value,
                    "summary": summary,
                    "action": "complete_task"
                }
            )
            
        except Exception as e:
            return MCPToolResult(
                success=False,
                error_message=f"Failed to complete task: {str(e)}"
            )
    
    
    def _calculate_recursion_depth(self, task: Task) -> int:
        """Calculate the recursion depth of this task"""
        # TODO: Implement proper recursion depth calculation
        # This would traverse up the parent task chain
        return 0 if not task.parent_task_id else 1
    
    async def _log_message(self, message_type: MessageType, content: str, metadata: Dict[str, Any] = None):
        """Log a message for this task"""
        message = Message(
            task_id=self.task_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        await database.messages.create(message)
        self.messages_logged += 1
    
    async def _complete_successfully(self, result: str) -> AgentExecutionResult:
        """Complete agent execution successfully"""
        execution_time = time.time() - self.start_time if self.start_time else 0
        
        return AgentExecutionResult(
            status=TaskStatus.COMPLETE,
            result=result,
            spawned_tasks=self.spawned_tasks,
            tool_calls_made=self.tool_calls_made,
            execution_time_seconds=execution_time
        )
    
    async def _complete_with_error(self, error_message: str) -> AgentExecutionResult:
        """Complete agent execution with error"""
        execution_time = time.time() - self.start_time if self.start_time else 0
        
        # Broadcast error message
        await self._broadcast_message(
            WebSocketMessage(
                type=WSMessageType.AGENT_ERROR,
                task_id=self.task_id,
                tree_id=self.tree_id,
                agent_name=self.execution_context.agent.name if self.execution_context else "Unknown",
                content={"error": error_message}
            )
        )
        
        # Update task status to failed
        await database.tasks.update_status(
            self.task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
        
        await self._log_message(
            MessageType.ERROR,
            f"Task failed: {error_message}",
            {"execution_error": True}
        )
        
        return AgentExecutionResult(
            status=TaskStatus.FAILED,
            error_message=error_message,
            spawned_tasks=self.spawned_tasks,
            tool_calls_made=self.tool_calls_made,
            execution_time_seconds=execution_time
        )
    
    async def _broadcast_message(self, message: WebSocketMessage):
        """Broadcast a WebSocket message through the task manager"""
        if self.task_manager:
            await self.task_manager.broadcast_message(message)
    
    async def _check_step_mode(self, checkpoint: str):
        """Check if step mode is active and pause if needed"""
        if not self.task_manager:
            return
        
        # Check if step mode is active for this task's tree
        if self.task_manager.is_step_mode_active(self.tree_id):
            # Create pause event
            pause_event = asyncio.Event()
            self.task_manager.paused_agents[self.task_id] = pause_event
            
            # Broadcast pause message
            await self._broadcast_message(
                MessageBuilder.step_pause(
                    self.task_id,
                    self.tree_id,
                    self.execution_context.agent.name,
                    f"Paused at checkpoint: {checkpoint}"
                )
            )
            
            # Wait for continue signal
            await pause_event.wait()