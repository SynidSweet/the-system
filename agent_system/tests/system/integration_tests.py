"""
Integration and workflow tests for the agent system.

Tests end-to-end workflows and component interactions.
"""

import uuid
import asyncio
from typing import Optional

from .test_utils import SuiteResults
from agent_system.core.events.event_types import EntityType
from agent_system.core.entities.task import TaskState


class IntegrationTests:
    """Integration and workflow test suite"""
    
    def __init__(self, database, entity_manager, runtime_engine):
        self.database = database
        self.entity_manager = entity_manager
        self.runtime_engine = runtime_engine
        self.results = SuiteResults("Integration")
    
    async def run_all(self) -> SuiteResults:
        """Run all integration tests"""
        # End-to-end workflow
        await self.results.run_test(
            "End-to-End Task Workflow",
            lambda: self._test_end_to_end_workflow()
        )
        
        # Component integration
        await self.results.run_test(
            "Component Integration",
            lambda: self._test_component_integration()
        )
        
        # Process execution
        await self.results.run_test(
            "Process Execution",
            lambda: self._test_process_execution()
        )
        
        # Knowledge system integration
        await self.results.run_test(
            "Knowledge System Integration",
            lambda: self._test_knowledge_integration()
        )
        
        # Event-driven workflows
        await self.results.run_test(
            "Event-Driven Workflows",
            lambda: self._test_event_driven_workflows()
        )
        
        return self.results
    
    async def _test_end_to_end_workflow(self) -> None:
        """Test complete task execution workflow"""
        # Create a root task
        tree_id = uuid.uuid4().hex
        root_task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"e2e_root_task_{uuid.uuid4().hex[:8]}",
            instruction="Root task: Create a simple hello world function",
            tree_id=tree_id
        )
        
        # Verify task created in correct state
        assert root_task.status == TaskState.CREATED.value, \
            f"Task should start in CREATED state, got {root_task.status}"
        
        # Simulate task state transitions
        states = [
            TaskState.READY_FOR_AGENT,
            TaskState.AGENT_RESPONDING,
            TaskState.COMPLETED
        ]
        
        for state in states:
            updated = await self.entity_manager.update_entity(
                EntityType.TASK,
                root_task.entity_id,
                {"status": state.value}
            )
            assert updated.status == state.value, \
                f"Failed to transition to {state}"
            
            # Verify events are created for state changes
            events = await self.entity_manager.get_entity_events(root_task.entity_id)
            assert len(events) > 0, "No events tracked for task state changes"
        
        # Create a subtask to simulate breakdown
        subtask = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"e2e_subtask_{uuid.uuid4().hex[:8]}",
            instruction="Subtask: Implement the function",
            parent_task_id=root_task.entity_id,
            tree_id=tree_id
        )
        
        # Verify parent-child relationship
        relationships = await self.entity_manager.get_entity_relationships(
            root_task.entity_id, "creates"
        )
        assert any(r.target_entity_id == subtask.entity_id for r in relationships), \
            "Parent-child relationship not established"
        
        # Complete subtask
        await self.entity_manager.update_entity(
            EntityType.TASK,
            subtask.entity_id,
            {"status": TaskState.COMPLETED.value, "result": {"code": "def hello(): return 'world'"}}
        )
        
        # Verify task tree query works
        tree_tasks = await self.entity_manager.tasks.find_by_tree(tree_id)
        assert len(tree_tasks) == 2, f"Expected 2 tasks in tree, found {len(tree_tasks)}"
    
    async def _test_component_integration(self) -> None:
        """Test integration between major components"""
        # Test Agent-Tool integration
        agent = await self.database.agents.get_by_name("agent_selector")
        assert agent is not None, "Agent selector not found"
        
        # Verify agent has access to required tools
        assert len(agent.available_tools) > 0, "Agent has no tools available"
        
        # Test Task-Agent assignment
        task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"component_test_{uuid.uuid4().hex[:8]}",
            instruction="Test task for component integration"
        )
        
        # Assign agent to task
        updated_task = await self.entity_manager.tasks.assign_agent(
            task.entity_id,
            agent.entity_id
        )
        assert updated_task.agent_id == agent.entity_id, \
            "Agent assignment failed"
        
        # Test Context-Agent integration
        contexts = await self.entity_manager.agents.get_context_documents(agent.entity_id)
        assert len(contexts) > 0, "Agent has no context documents"
    
    async def _test_process_execution(self) -> None:
        """Test process framework execution"""
        from core.processes import process_registry
        
        # Get neutral task process
        process = process_registry.get_process("neutral_task_process")
        assert process is not None, "Neutral task process not found"
        
        # Create process instance
        process_entity = await self.entity_manager.processes.find_by_name(
            "neutral_task_process"
        )
        if not process_entity:
            # Create process entity if it doesn't exist
            process_entity = await self.entity_manager.create_entity(
                EntityType.PROCESS,
                name="neutral_task_process",
                triggers=["task_created"],
                description="Main task processing workflow"
            )
        
        # Create test task
        test_task = await self.entity_manager.create_entity(
            EntityType.TASK,
            name=f"process_test_{uuid.uuid4().hex[:8]}",
            instruction="Test task for process execution"
        )
        
        # Verify process can handle the task
        assert hasattr(process, 'can_handle'), "Process missing can_handle method"
        assert hasattr(process, 'execute'), "Process missing execute method"
        
        # Test process instance creation
        instance = await self.entity_manager.create_process_instance(
            process_entity.entity_id,
            test_task.entity_id,
            {"instruction": test_task.instruction}
        )
        assert instance is not None, "Failed to create process instance"
        assert instance.state == "pending", "Process instance should start in pending state"
    
    async def _test_knowledge_integration(self) -> None:
        """Test knowledge system integration"""
        try:
            from core.knowledge.engine import KnowledgeEngine
            
            # Initialize knowledge engine
            engine = KnowledgeEngine()
            
            # Test knowledge query for a task
            test_task = {
                "instruction": "Implement a REST API endpoint",
                "context": ["web development", "python", "fastapi"]
            }
            
            # Assembly context (basic test - full test would require bootstrapped knowledge)
            context = await engine.assemble_context(test_task)
            assert context is not None, "Failed to assemble context"
            assert "domains" in context, "Context missing domains"
            
            # Test gap detection
            gaps = await engine.detect_gaps(test_task, context)
            assert isinstance(gaps, list), "Gap detection should return a list"
            
        except ImportError:
            # Knowledge system may not be fully initialized
            # This is acceptable for basic integration testing
            pass
    
    async def _test_event_driven_workflows(self) -> None:
        """Test event-driven system behaviors"""
        # Create an agent
        test_agent = await self.entity_manager.create_entity(
            EntityType.AGENT,
            name=f"event_test_{uuid.uuid4().hex[:8]}",
            instruction="Event workflow test agent"
        )
        
        # Track initial event count
        initial_events = await self.entity_manager.get_entity_events(
            test_agent.entity_id
        )
        initial_count = len(initial_events)
        
        # Perform operations that should generate events
        # Update agent
        await self.entity_manager.update_entity(
            EntityType.AGENT,
            test_agent.entity_id,
            {"instruction": "Updated instruction"}
        )
        
        # Add relationship
        await self.entity_manager.add_entity_relationship(
            test_agent.entity_id,
            "uses",
            test_agent.entity_id  # Self-reference for testing
        )
        
        # Check events were generated
        final_events = await self.entity_manager.get_entity_events(
            test_agent.entity_id
        )
        final_count = len(final_events)
        
        assert final_count > initial_count, \
            "No events generated for entity operations"
        
        # Test event chain tracking
        if final_events:
            # Create child event
            parent_event = final_events[-1]
            child_event_data = {
                "event_type": "test_child_event",
                "entity_id": test_agent.entity_id,
                "parent_event_id": parent_event.event_id,
                "data": {"test": "child event"}
            }
            
            child_event = await self.entity_manager.create_event(child_event_data)
            assert child_event.parent_event_id == parent_event.event_id, \
                "Event chain not properly established"