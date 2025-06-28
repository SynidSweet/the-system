"""
Health and connectivity tests for the agent system.

Tests system components are accessible and properly configured.
"""

from typing import List
from pathlib import Path

from .test_utils import (
    SuiteResults, TestResult,
    assert_database_accessible, assert_tool_registered, assert_agent_exists
)


class HealthTests:
    """Health and connectivity test suite"""
    
    def __init__(self, database, tool_registry):
        self.database = database
        self.tool_registry = tool_registry
        self.results = SuiteResults("Health")
    
    async def run_all(self) -> SuiteResults:
        """Run all health tests"""
        # Database connectivity
        await self.results.run_test(
            "Database Connectivity",
            lambda: self._test_database_connectivity()
        )
        
        # Agent configuration
        await self.results.run_test(
            "Agent Configuration",
            lambda: self._test_agent_configuration()
        )
        
        # Tool registry
        await self.results.run_test(
            "Tool Registry",
            lambda: self._test_tool_registry()
        )
        
        # Context documents
        await self.results.run_test(
            "Context Documents",
            lambda: self._test_context_documents()
        )
        
        # System initialization
        await self.results.run_test(
            "System Initialization",
            lambda: self._test_system_initialization()
        )
        
        return self.results
    
    async def _test_database_connectivity(self) -> None:
        """Test database connection and basic operations"""
        await assert_database_accessible(self.database)
        
        # Additional health checks
        tables = await self.database.get_tables()
        required_tables = ["entities", "agents", "tasks", "tools", "context_documents"]
        for table in required_tables:
            assert table in tables, f"Required table '{table}' not found"
    
    async def _test_agent_configuration(self) -> None:
        """Test that all expected agents are configured"""
        expected_agents = [
            "agent_selector", "task_breakdown", "context_addition", "tool_addition",
            "task_evaluator", "documentation_agent", "summary_agent", "review_agent"
        ]
        
        for agent_name in expected_agents:
            await assert_agent_exists(agent_name, self.database)
    
    async def _test_tool_registry(self) -> None:
        """Test that core tools are registered"""
        core_tools = [
            "break_down_task", "create_subtask", "end_task",
            "need_more_context", "need_more_tools"
        ]
        
        for tool_name in core_tools:
            await assert_tool_registered(tool_name, self.tool_registry)
        
        # Verify tool count
        all_tools = self.tool_registry.get_all_tools()
        assert len(all_tools) >= len(core_tools), \
            f"Expected at least {len(core_tools)} tools, found {len(all_tools)}"
    
    async def _test_context_documents(self) -> None:
        """Test that context documents are available"""
        docs = await self.database.context_documents.get_all()
        assert len(docs) > 0, "No context documents found"
        
        # Check for essential documents
        doc_names = [doc.name for doc in docs]
        essential_docs = [
            "system_overview", "process_guidelines", "agent_instructions"
        ]
        
        missing_docs = [doc for doc in essential_docs if not any(doc in name for name in doc_names)]
        assert len(missing_docs) == 0, f"Missing essential documents: {missing_docs}"
    
    async def _test_system_initialization(self) -> None:
        """Test that system components are properly initialized"""
        # Check process registry
        from core.processes import process_registry
        processes = process_registry.get_all_processes()
        assert len(processes) > 0, "No processes registered"
        
        # Check for critical processes
        critical_processes = ["neutral_task_process", "tool_triggered_process"]
        for process_name in critical_processes:
            process = process_registry.get_process(process_name)
            assert process is not None, f"Critical process '{process_name}' not found"
        
        # Check configuration
        from config.settings import settings
        assert settings.DEFAULT_MODEL_PROVIDER is not None, "No default model provider configured"
        assert settings.DATABASE_URL is not None, "No database URL configured"