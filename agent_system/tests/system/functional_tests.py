"""
Functional capability tests for the agent system.

Tests core functionality like tool execution, database operations, and agent instantiation.
"""

import uuid
from datetime import datetime

from .test_utils import SuiteResults, TestResult
from core.entities.enums import EntityType, TaskState


class FunctionalTests:
    """Functional capability test suite"""
    
    def __init__(self, database, tool_registry, entity_manager):
        self.database = database
        self.tool_registry = tool_registry
        self.entity_manager = entity_manager
        self.results = SuiteResults("Functional")
    
    async def run_all(self) -> SuiteResults:
        """Run all functional tests"""
        # Core tool execution
        await self.results.run_test(
            "Core Tool Execution",
            lambda: self._test_core_tools()
        )
        
        # System tool execution
        await self.results.run_test(
            "System Tool Execution", 
            lambda: self._test_system_tools()
        )
        
        # Database operations
        await self.results.run_test(
            "Database Operations",
            lambda: self._test_database_operations()
        )
        
        # Agent instantiation
        await self.results.run_test(
            "Agent Instantiation",
            lambda: self._test_agent_instantiation()
        )
        
        # Task lifecycle
        await self.results.run_test(
            "Task Lifecycle",
            lambda: self._test_task_lifecycle()
        )
        
        # Event tracking
        await self.results.run_test(
            "Event Tracking",
            lambda: self._test_event_tracking()
        )
        
        return self.results
    
    async def _test_core_tools(self) -> None:
        """Test core MCP tool execution"""
        # Test break_down_task tool
        tool = self.tool_registry.get_tool("break_down_task")
        assert tool is not None, "break_down_task tool not found"
        
        # Create a test task for breakdown
        test_task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"test_task_{uuid.uuid4().hex[:8]}",
            instruction="Test task for functional testing"
        )
        
        # Execute tool (basic validation - full execution would require runtime)
        assert hasattr(tool, 'execute'), "Tool missing execute method"
        assert hasattr(tool, 'get_schema'), "Tool missing get_schema method"
        
        # Verify schema
        schema = tool.get_schema()
        assert "name" in schema, "Tool schema missing name"
        assert "parameters" in schema, "Tool schema missing parameters"
    
    async def _test_system_tools(self) -> None:
        """Test system tool execution"""
        # Test entity manager tool
        tool = self.tool_registry.get_tool("entity_manager")
        if tool is not None:  # System tools may be optional
            schema = tool.get_schema()
            assert "operations" in schema["parameters"]["properties"], \
                "Entity manager tool missing operations parameter"
    
    async def _test_database_operations(self) -> None:
        """Test CRUD operations on database"""
        # Create test agent
        test_name = f"test_agent_{uuid.uuid4().hex[:8]}"
        agent = await self.entity_manager.create_entity(
            EntityType.AGENT,
            name=test_name,
            instruction="Test agent for functional testing",
            available_tools=["break_down_task"]
        )
        
        assert agent is not None, "Failed to create agent"
        assert agent.name == test_name, "Agent name mismatch"
        
        # Read agent
        retrieved = await self.entity_manager.get_entity(EntityType.AGENT, agent.entity_id)
        assert retrieved is not None, "Failed to retrieve agent"
        assert retrieved.entity_id == agent.entity_id, "Retrieved wrong agent"
        
        # Update agent
        updated = await self.entity_manager.update_entity(
            EntityType.AGENT,
            agent.entity_id,
            {"instruction": "Updated instruction"}
        )
        assert updated.instruction == "Updated instruction", "Failed to update agent"
        
        # List agents
        agents = await self.entity_manager.list_entities(EntityType.AGENT)
        assert any(a.entity_id == agent.entity_id for a in agents), \
            "Created agent not in list"
        
        # Cleanup - soft delete
        await self.entity_manager.update_entity(
            EntityType.AGENT,
            agent.entity_id,
            {"state": "inactive"}
        )
    
    async def _test_agent_instantiation(self) -> None:
        """Test agent runtime instantiation"""
        from core.universal_agent_runtime import UniversalAgentRuntime
        
        # Get a test agent
        agents = await self.database.agents.get_all_active()
        assert len(agents) > 0, "No active agents found"
        
        test_agent = agents[0]
        
        # Create runtime instance
        runtime = UniversalAgentRuntime(
            agent_entity=test_agent,
            task_entity=None,  # No task for basic instantiation test
            entity_manager=self.entity_manager
        )
        
        assert runtime is not None, "Failed to create agent runtime"
        assert runtime.agent_entity.entity_id == test_agent.entity_id, \
            "Runtime has wrong agent"
        assert hasattr(runtime, 'execute'), "Runtime missing execute method"
    
    async def _test_task_lifecycle(self) -> None:
        """Test task creation and state transitions"""
        # Create parent task
        parent_task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"parent_task_{uuid.uuid4().hex[:8]}",
            instruction="Parent task for testing",
            tree_id=uuid.uuid4().hex
        )
        
        # Create subtask
        subtask = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"subtask_{uuid.uuid4().hex[:8]}",
            instruction="Subtask for testing",
            parent_task_id=parent_task.entity_id,
            tree_id=parent_task.tree_id
        )
        
        assert subtask.parent_task_id == parent_task.entity_id, \
            "Subtask parent relationship not set"
        assert subtask.tree_id == parent_task.tree_id, \
            "Subtask tree_id mismatch"
        
        # Test state transitions
        states = [
            TaskState.READY_FOR_AGENT,
            TaskState.AGENT_RESPONDING,
            TaskState.COMPLETED
        ]
        
        for state in states:
            updated = await self.entity_manager.update_entity(
                EntityType.TASK,
                subtask.entity_id,
                {"status": state.value}
            )
            assert updated.status == state.value, f"Failed to transition to {state}"
    
    async def _test_event_tracking(self) -> None:
        """Test event creation and tracking"""
        # Create a test event
        test_entity = await self.entity_manager.create_entity(
            EntityType.AGENT,
            name=f"event_test_agent_{uuid.uuid4().hex[:8]}",
            instruction="Agent for event testing"
        )
        
        # Create event
        event_data = {
            "event_type": "test_event",
            "entity_id": test_entity.entity_id,
            "data": {"test": "data"},
            "timestamp": datetime.now()
        }
        
        event = await self.entity_manager.create_event(event_data)
        assert event is not None, "Failed to create event"
        
        # Query events
        events = await self.entity_manager.get_entity_events(test_entity.entity_id)
        assert len(events) > 0, "No events found for entity"
        assert any(e.event_type == "test_event" for e in events), \
            "Test event not found in entity events"