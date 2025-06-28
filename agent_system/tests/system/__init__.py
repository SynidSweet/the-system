"""
System test suite for the agent system.

This package provides modular testing capabilities organized by test type:
- health_tests: System health and connectivity checks
- functional_tests: Core functionality validation
- performance_tests: Performance and efficiency metrics
- integration_tests: End-to-end workflow testing

Usage:
    # Run all tests
    python -m tests.system.test_runner
    
    # Run specific suite
    python -m tests.system.test_runner --suite health
"""

from .test_utils import (
    TestResult,
    SuiteResults,
    TestReporter,
    PerformanceMonitor,
    time_test,
    assert_database_accessible,
    assert_tool_registered,
    assert_agent_exists
)

from .health_tests import HealthTests
from .functional_tests import FunctionalTests
from .performance_tests import PerformanceTests
from .integration_tests import IntegrationTests
from .test_runner import SystemTestRunner

__all__ = [
    # Test utilities
    "TestResult",
    "SuiteResults", 
    "TestReporter",
    "PerformanceMonitor",
    "time_test",
    "assert_database_accessible",
    "assert_tool_registered",
    "assert_agent_exists",
    
    # Test suites
    "HealthTests",
    "FunctionalTests",
    "PerformanceTests",
    "IntegrationTests",
    
    # Runner
    "SystemTestRunner"
]