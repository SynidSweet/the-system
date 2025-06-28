"""
Test utilities and common patterns for system testing.

This module provides shared utilities to reduce duplication across test suites.
"""

import time
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime


class TestResult:
    """Encapsulates a test result with metadata"""
    
    def __init__(self, name: str, passed: bool, message: str, duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "duration": self.duration
        }


class SuiteResults:
    """Manages test suite results with automatic aggregation"""
    
    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self.tests: List[TestResult] = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
    
    def add_test(self, result: TestResult) -> None:
        """Add a test result and update counters"""
        self.tests.append(result)
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
    
    async def run_test(self, test_name: str, test_func: Callable) -> TestResult:
        """Run a test function and automatically record the result"""
        start_time = time.time()
        try:
            # Run the test function
            await test_func()
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                passed=True,
                message="Test passed successfully",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                passed=False,
                message=f"Failed: {str(e)}",
                duration=duration
            )
        
        self.add_test(result)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suite results to dictionary format"""
        return {
            "tests": [test.to_dict() for test in self.tests],
            "passed": self.passed,
            "failed": self.failed,
            "duration": time.time() - self.start_time
        }
    
    def print_summary(self) -> None:
        """Print a summary of the suite results"""
        status = "✅ PASSED" if self.failed == 0 else "❌ FAILED"
        print(f"{self.suite_name} Tests: {status} ({self.passed}/{len(self.tests)})")
        
        # Print failed tests for debugging
        if self.failed > 0:
            print(f"\nFailed {self.suite_name} tests:")
            for test in self.tests:
                if not test.passed:
                    print(f"  - {test.name}: {test.message}")


class TestReporter:
    """Generates comprehensive test reports"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "suites": {},
            "duration": 0
        }
        self.start_time = time.time()
    
    def add_suite_results(self, suite_results: SuiteResults) -> None:
        """Add suite results to the overall report"""
        suite_dict = suite_results.to_dict()
        self.results["suites"][suite_results.suite_name] = suite_dict
        self.results["tests_run"] += len(suite_results.tests)
        self.results["tests_passed"] += suite_results.passed
        self.results["tests_failed"] += suite_results.failed
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate the final test report"""
        self.results["duration"] = time.time() - self.start_time
        self.results["success"] = self.results["tests_failed"] == 0
        return self.results
    
    def print_summary(self) -> None:
        """Print overall test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = self.results["tests_run"]
        passed = self.results["tests_passed"]
        failed = self.results["tests_failed"]
        duration = self.results["duration"]
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed} ({passed/total_tests*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total_tests*100:.1f}%)")
        print(f"Duration: {duration:.2f}s")
        
        if failed == 0:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print(f"\n❌ {failed} TESTS FAILED")
            print("\nFailed tests by suite:")
            for suite_name, suite_data in self.results["suites"].items():
                failed_tests = [t for t in suite_data["tests"] if not t["passed"]]
                if failed_tests:
                    print(f"\n{suite_name}:")
                    for test in failed_tests:
                        print(f"  - {test['name']}: {test['message']}")


# Test timing utilities
def time_test(func: Callable) -> Callable:
    """Decorator to time test execution"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        if hasattr(result, '__setitem__'):
            result['duration'] = duration
        return result
    return wrapper


# Common test assertions
async def assert_database_accessible(database) -> None:
    """Assert that database is accessible"""
    await database.initialize()
    agents = await database.agents.get_all_active()
    assert isinstance(agents, list), "Database query should return a list"


async def assert_tool_registered(tool_name: str, tool_registry) -> None:
    """Assert that a tool is properly registered"""
    tool = tool_registry.get_tool(tool_name)
    assert tool is not None, f"Tool {tool_name} not found in registry"
    assert hasattr(tool, 'execute'), f"Tool {tool_name} missing execute method"


async def assert_agent_exists(agent_name: str, database) -> None:
    """Assert that an agent exists in the database"""
    agent = await database.agents.get_by_name(agent_name)
    assert agent is not None, f"Agent {agent_name} not found in database"
    assert agent.state == "active", f"Agent {agent_name} is not active"


# Performance measurement utilities
class PerformanceMonitor:
    """Monitor performance metrics during tests"""
    
    def __init__(self):
        self.metrics = {}
    
    async def measure(self, name: str, func: Callable, threshold: float = None) -> Dict[str, Any]:
        """Measure function execution time and compare to threshold"""
        start = time.time()
        result = await func()
        duration = time.time() - start
        
        passed = True
        message = f"Completed in {duration:.3f}s"
        
        if threshold is not None:
            if duration > threshold:
                passed = False
                message = f"Too slow: {duration:.3f}s > {threshold}s threshold"
            else:
                message = f"Within threshold: {duration:.3f}s < {threshold}s"
        
        self.metrics[name] = {
            "duration": duration,
            "passed": passed,
            "threshold": threshold
        }
        
        return {
            "name": name,
            "passed": passed,
            "message": message,
            "duration": duration,
            "metrics": {"threshold": threshold} if threshold else {}
        }