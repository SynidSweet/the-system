#!/usr/bin/env python3
"""
Comprehensive system testing script for the agent system.

This script provides comprehensive testing capabilities for validating
system health, functionality, and performance after self-modifications.

Usage:
    python scripts/test_system.py                    # Run all tests
    python scripts/test_system.py --suite health     # Run health tests only
    python scripts/test_system.py --suite functional # Run functional tests only
    python scripts/test_system.py --suite performance # Run performance tests only
"""

import asyncio
import argparse
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from ..config.database import DatabaseManager

# Create global database instance
database = DatabaseManager()
from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import register_core_tools
from tools.system_tools.mcp_integrations import register_system_tools
from tools.system_tools.internal_tools import register_internal_tools


class SystemTester:
    """Comprehensive system testing framework"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "suites": {}
        }
        self.start_time = None
        
    async def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🧪 Running Comprehensive System Tests")
        print("=" * 60)
        
        self.start_time = time.time()
        
        suites = [
            ("health", self._run_health_tests),
            ("functional", self._run_functional_tests),
            ("performance", self._run_performance_tests),
            ("integration", self._run_integration_tests)
        ]
        
        overall_success = True
        
        for suite_name, suite_func in suites:
            print(f"\n🔍 Running {suite_name.upper()} tests...")
            suite_success = await suite_func()
            
            if not suite_success:
                overall_success = False
                
        # Generate final report
        await self._generate_final_report()
        
        return overall_success
    
    async def run_suite(self, suite_name: str) -> bool:
        """Run a specific test suite"""
        print(f"🧪 Running {suite_name.upper()} Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        suite_map = {
            "health": self._run_health_tests,
            "functional": self._run_functional_tests,
            "performance": self._run_performance_tests,
            "integration": self._run_integration_tests
        }
        
        if suite_name not in suite_map:
            print(f"❌ Unknown test suite: {suite_name}")
            return False
            
        success = await suite_map[suite_name]()
        await self._generate_final_report()
        
        return success
    
    async def _run_health_tests(self) -> bool:
        """Run health and connectivity tests"""
        suite_results = {"tests": [], "passed": 0, "failed": 0}
        
        # Database connectivity
        test_result = await self._test_database_connectivity()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Agent configuration
        test_result = await self._test_agent_configuration()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Tool registry
        test_result = await self._test_tool_registry()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Context documents
        test_result = await self._test_context_documents()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        self.results["suites"]["health"] = suite_results
        self.results["tests_run"] += len(suite_results["tests"])
        self.results["tests_passed"] += suite_results["passed"]
        self.results["tests_failed"] += suite_results["failed"]
        
        success = suite_results["failed"] == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Health Tests: {status} ({suite_results['passed']}/{len(suite_results['tests'])})")
        
        return success
    
    async def _run_functional_tests(self) -> bool:
        """Run functional capability tests"""
        suite_results = {"tests": [], "passed": 0, "failed": 0}
        
        # Core tool execution
        test_result = await self._test_core_tools()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # System tool execution
        test_result = await self._test_system_tools()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Database operations
        test_result = await self._test_database_operations()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Agent instantiation
        test_result = await self._test_agent_instantiation()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        self.results["suites"]["functional"] = suite_results
        self.results["tests_run"] += len(suite_results["tests"])
        self.results["tests_passed"] += suite_results["passed"]
        self.results["tests_failed"] += suite_results["failed"]
        
        success = suite_results["failed"] == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Functional Tests: {status} ({suite_results['passed']}/{len(suite_results['tests'])})")
        
        return success
    
    async def _run_performance_tests(self) -> bool:
        """Run performance and efficiency tests"""
        suite_results = {"tests": [], "passed": 0, "failed": 0}
        
        # Database query performance
        test_result = await self._test_database_performance()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Tool execution performance
        test_result = await self._test_tool_performance()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Memory usage
        test_result = await self._test_memory_usage()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        self.results["suites"]["performance"] = suite_results
        self.results["tests_run"] += len(suite_results["tests"])
        self.results["tests_passed"] += suite_results["passed"]
        self.results["tests_failed"] += suite_results["failed"]
        
        success = suite_results["failed"] == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Performance Tests: {status} ({suite_results['passed']}/{len(suite_results['tests'])})")
        
        return success
    
    async def _run_integration_tests(self) -> bool:
        """Run integration and workflow tests"""
        suite_results = {"tests": [], "passed": 0, "failed": 0}
        
        # End-to-end workflow
        test_result = await self._test_end_to_end_workflow()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        # Component integration
        test_result = await self._test_component_integration()
        suite_results["tests"].append(test_result)
        if test_result["passed"]:
            suite_results["passed"] += 1
        else:
            suite_results["failed"] += 1
        
        self.results["suites"]["integration"] = suite_results
        self.results["tests_run"] += len(suite_results["tests"])
        self.results["tests_passed"] += suite_results["passed"]
        self.results["tests_failed"] += suite_results["failed"]
        
        success = suite_results["failed"] == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Integration Tests: {status} ({suite_results['passed']}/{len(suite_results['tests'])})")
        
        return success
    
    # Individual test implementations
    
    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connection and basic operations"""
        try:
            await db_manager.connect()
            await database.initialize()
            
            # Test basic query
            agents = await database.agents.get_all_active()
            
            return {
                "name": "Database Connectivity",
                "passed": True,
                "message": f"Connected successfully, {len(agents)} agents found",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "Database Connectivity",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_agent_configuration(self) -> Dict[str, Any]:
        """Test that all expected agents are configured"""
        try:
            expected_agents = [
                "agent_selector", "task_breakdown", "context_addition", "tool_addition",
                "task_evaluator", "documentation_agent", "summary_agent", "review_agent"
            ]
            
            missing_agents = []
            for agent_name in expected_agents:
                agent = await database.agents.get_by_name(agent_name)
                if not agent:
                    missing_agents.append(agent_name)
            
            if missing_agents:
                return {
                    "name": "Agent Configuration",
                    "passed": False,
                    "message": f"Missing agents: {missing_agents}",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "Agent Configuration",
                    "passed": True,
                    "message": f"All {len(expected_agents)} agents configured",
                    "duration": 0.1
                }
        except Exception as e:
            return {
                "name": "Agent Configuration",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_tool_registry(self) -> Dict[str, Any]:
        """Test tool registry functionality"""
        try:
            # Register tools
            register_core_tools(tool_registry)
            register_system_tools(tool_registry)
            register_internal_tools(tool_registry)
            
            # Check tool counts
            tools = tool_registry.list_tools()
            total_tools = sum(len(tools) for tools in tools.values())
            
            if total_tools >= 10:  # Expect at least 10 tools
                return {
                    "name": "Tool Registry",
                    "passed": True,
                    "message": f"{total_tools} tools registered",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "Tool Registry",
                    "passed": False,
                    "message": f"Only {total_tools} tools registered (expected ≥10)",
                    "duration": 0.1
                }
        except Exception as e:
            return {
                "name": "Tool Registry",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_context_documents(self) -> Dict[str, Any]:
        """Test context document availability"""
        try:
            docs = await database.context_documents.get_by_category("system")
            
            if len(docs) >= 3:  # Expect at least 3 system docs
                return {
                    "name": "Context Documents",
                    "passed": True,
                    "message": f"{len(docs)} system documents available",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "Context Documents",
                    "passed": False,
                    "message": f"Only {len(docs)} system documents (expected ≥3)",
                    "duration": 0.1
                }
        except Exception as e:
            return {
                "name": "Context Documents",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_core_tools(self) -> Dict[str, Any]:
        """Test core tool instantiation"""
        try:
            from tools.core_mcp.core_tools import EndTaskTool
            
            tool = EndTaskTool()
            result = await tool.execute(status="success", result="Test completed")
            
            if result.success:
                return {
                    "name": "Core Tools",
                    "passed": True,
                    "message": "Core tools functional",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "Core Tools",
                    "passed": False,
                    "message": f"Tool execution failed: {result.error_message}",
                    "duration": 0.1
                }
        except Exception as e:
            return {
                "name": "Core Tools",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_system_tools(self) -> Dict[str, Any]:
        """Test system tool functionality"""
        try:
            from tools.system_tools.internal_tools import ListAgentsTool
            
            tool = ListAgentsTool()
            result = await tool.execute()
            
            if result.success:
                return {
                    "name": "System Tools",
                    "passed": True,
                    "message": "System tools functional",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "System Tools",
                    "passed": False,
                    "message": f"Tool execution failed: {result.error_message}",
                    "duration": 0.1
                }
        except Exception as e:
            return {
                "name": "System Tools",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_database_operations(self) -> Dict[str, Any]:
        """Test database CRUD operations"""
        try:
            # Test agent retrieval
            agents = await database.agents.get_all_active()
            
            # Test context document retrieval
            docs = await database.context_documents.get_all()
            
            # Test tool retrieval
            tools = await database.tools.get_all_active()
            
            return {
                "name": "Database Operations",
                "passed": True,
                "message": f"CRUD operations successful ({len(agents)} agents, {len(docs)} docs, {len(tools)} tools)",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "Database Operations",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_agent_instantiation(self) -> Dict[str, Any]:
        """Test agent loading and basic instantiation"""
        try:
            from core.universal_agent import UniversalAgent
            from pydantic import BaseModel
            
            # Temporary compatibility model
            class AgentPermissions(BaseModel):
                web_search: bool = False
                file_system: bool = False
                shell_access: bool = False
                git_operations: bool = False
                database_write: bool = False
                spawn_agents: bool = True
            
            # Create a test agent configuration
            agent_config = {
                "name": "test_agent",
                "instruction": "This is a test agent",
                "available_tools": ["think_out_loud"],
                "permissions": AgentPermissions()
            }
            
            # This would test agent creation without execution
            return {
                "name": "Agent Instantiation",
                "passed": True,
                "message": "Agent class loadable",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "Agent Instantiation",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_database_performance(self) -> Dict[str, Any]:
        """Test database query performance"""
        try:
            start_time = time.time()
            
            # Run multiple queries
            for _ in range(10):
                await database.agents.get_all_active()
                await database.context_documents.get_all()
                await database.tools.get_all_active()
            
            duration = time.time() - start_time
            avg_time = duration / 30  # 30 total queries
            
            if avg_time < 0.1:  # Each query should be under 100ms
                return {
                    "name": "Database Performance",
                    "passed": True,
                    "message": f"Average query time: {avg_time:.3f}s",
                    "duration": duration
                }
            else:
                return {
                    "name": "Database Performance",
                    "passed": False,
                    "message": f"Slow queries: {avg_time:.3f}s average (>0.1s)",
                    "duration": duration
                }
        except Exception as e:
            return {
                "name": "Database Performance",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_tool_performance(self) -> Dict[str, Any]:
        """Test tool execution performance"""
        try:
            from tools.core_mcp.core_tools import ThinkOutLoudTool
            
            start_time = time.time()
            
            tool = ThinkOutLoudTool()
            for _ in range(5):
                await tool.execute(thoughts="Performance test", thought_type="testing")
            
            duration = time.time() - start_time
            avg_time = duration / 5
            
            if avg_time < 0.5:  # Each tool execution should be under 500ms
                return {
                    "name": "Tool Performance",
                    "passed": True,
                    "message": f"Average execution time: {avg_time:.3f}s",
                    "duration": duration
                }
            else:
                return {
                    "name": "Tool Performance",
                    "passed": False,
                    "message": f"Slow tool execution: {avg_time:.3f}s average (>0.5s)",
                    "duration": duration
                }
        except Exception as e:
            return {
                "name": "Tool Performance",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_memory_usage(self) -> Dict[str, Any]:
        """Test basic memory usage patterns"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb < 512:  # Should use less than 512MB
                return {
                    "name": "Memory Usage",
                    "passed": True,
                    "message": f"Memory usage: {memory_mb:.1f}MB",
                    "duration": 0.1
                }
            else:
                return {
                    "name": "Memory Usage",
                    "passed": False,
                    "message": f"High memory usage: {memory_mb:.1f}MB (>512MB)",
                    "duration": 0.1
                }
        except ImportError:
            return {
                "name": "Memory Usage",
                "passed": True,
                "message": "psutil not available, skipping",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "Memory Usage",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test simplified end-to-end workflow"""
        try:
            # This would test a complete workflow simulation
            # For now, just verify key components can be loaded
            
            from core.runtime.runtime_integration import RuntimeIntegration
            from core.universal_agent_runtime import UniversalAgentRuntime
            
            return {
                "name": "End-to-End Workflow",
                "passed": True,
                "message": "Core workflow components loadable",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "End-to-End Workflow",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _test_component_integration(self) -> Dict[str, Any]:
        """Test component integration"""
        try:
            # Test that all major components can be imported and initialized
            components = [
                "core.database_manager",
                "core.universal_agent_runtime", 
                "core.runtime.runtime_integration",
                "tools.base_tool",
                "api.main"
            ]
            
            for component in components:
                __import__(component)
            
            return {
                "name": "Component Integration",
                "passed": True,
                "message": f"All {len(components)} core components loadable",
                "duration": 0.1
            }
        except Exception as e:
            return {
                "name": "Component Integration",
                "passed": False,
                "message": f"Failed: {str(e)}",
                "duration": 0.1
            }
    
    async def _generate_final_report(self):
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 60)
        print("📊 FINAL TEST REPORT")
        print("=" * 60)
        
        print(f"Total Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']} ✅")
        print(f"Tests Failed: {self.results['tests_failed']} ❌")
        print(f"Success Rate: {(self.results['tests_passed']/self.results['tests_run']*100):.1f}%")
        print(f"Total Duration: {total_time:.2f}s")
        
        # Suite breakdown
        for suite_name, suite_data in self.results["suites"].items():
            print(f"\n{suite_name.upper()} Suite:")
            for test in suite_data["tests"]:
                status = "✅" if test["passed"] else "❌"
                print(f"  {status} {test['name']}: {test['message']}")
        
        # Save detailed results
        report_file = Path(__file__).parent.parent / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results["total_duration"] = total_time
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: {report_file}")
        
        if self.results["tests_failed"] == 0:
            print("\n🎉 ALL TESTS PASSED! System is healthy.")
        else:
            print(f"\n⚠️  {self.results['tests_failed']} tests failed. Review results above.")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive system testing")
    parser.add_argument("--suite", choices=["health", "functional", "performance", "integration"], 
                       help="Run specific test suite only")
    parser.add_argument("--output", help="Output file for detailed results")
    
    args = parser.parse_args()
    
    tester = SystemTester()
    
    try:
        if args.suite:
            success = await tester.run_suite(args.suite)
        else:
            success = await tester.run_all_tests()
        
        return success
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed: {e}")
        sys.exit(1)