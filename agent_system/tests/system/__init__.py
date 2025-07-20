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

# Import test utilities (these should work)
try:
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
except ImportError as e:
    print(f"Warning: Could not import test_utils: {e}")

# Import test suites conditionally
try:
    from .health_tests import HealthTests
except ImportError as e:
    print(f"Warning: Could not import HealthTests: {e}")
    HealthTests = None

try:
    from .functional_tests import FunctionalTests
except ImportError as e:
    print(f"Warning: Could not import FunctionalTests: {e}")
    FunctionalTests = None

try:
    from .performance_tests import PerformanceTests
except ImportError as e:
    print(f"Warning: Could not import PerformanceTests: {e}")
    PerformanceTests = None

try:
    from .integration_tests import IntegrationTests
except ImportError as e:
    print(f"Warning: Could not import IntegrationTests: {e}")
    IntegrationTests = None

try:
    from .test_runner import SystemTestRunner
except ImportError as e:
    print(f"Warning: Could not import SystemTestRunner: {e}")
    SystemTestRunner = None

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