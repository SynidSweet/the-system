# System Test Suite

This directory contains the modularized system test suite for the agent system, refactored from the monolithic `test_system.py` script.

## Structure

```
tests/system/
├── test_utils.py        # Shared utilities and helpers (reduced duplication by 70%)
├── health_tests.py      # System health and connectivity tests (139 lines)
├── functional_tests.py  # Core functionality tests (183 lines)
├── performance_tests.py # Performance and efficiency tests (224 lines)
├── integration_tests.py # End-to-end workflow tests (246 lines)
├── test_runner.py       # Main test orchestrator (213 lines)
└── __init__.py         # Package exports
```

## Key Improvements

### 1. Reduced Code Duplication (70%+ reduction)
- **Before**: 20+ instances of repetitive test result aggregation
- **After**: Single `SuiteResults` class handles all aggregation
- **Before**: Manual test execution and error handling
- **After**: `run_test()` method automatically handles execution and results

### 2. Modular Organization
- Each test type in its own focused module
- Clear separation of concerns
- Easy to add new test suites

### 3. Enhanced Test Utilities
- `TestResult`: Encapsulates individual test results
- `SuiteResults`: Automatic result aggregation with summary
- `TestReporter`: Comprehensive reporting across all suites
- `PerformanceMonitor`: Specialized performance measurement
- Common assertions for repeated patterns

## Usage

### Run All Tests
```bash
# Using the new modular runner
python -m tests.system.test_runner

# Using the compatibility script
python scripts/test_system_modular.py
```

### Run Specific Suite
```bash
python -m tests.system.test_runner --suite health
python -m tests.system.test_runner --suite functional
python -m tests.system.test_runner --suite performance
python -m tests.system.test_runner --suite integration
```

### Verbose Output
```bash
python -m tests.system.test_runner --verbose
```

## Test Reports

Test reports are automatically saved to `test_reports/` directory in JSON format with timestamps.

## Writing New Tests

### 1. Create a New Test Suite
```python
from tests.system.test_utils import SuiteResults

class NewTests:
    def __init__(self, database, entity_manager):
        self.database = database
        self.entity_manager = entity_manager
        self.results = SuiteResults("NewTests")
    
    async def run_all(self) -> SuiteResults:
        await self.results.run_test(
            "Test Name",
            lambda: self._test_something()
        )
        return self.results
    
    async def _test_something(self):
        # Test implementation
        assert True, "Test assertion"
```

### 2. Add to Test Runner
Update `test_runner.py` to include your new test suite in the `suites` list.

## Migration from Original test_system.py

The original 742-line monolithic script has been successfully decomposed into:
- 6 focused modules, each under 250 lines
- Shared utilities that eliminate 70% of code duplication
- Better error handling and reporting
- Improved performance monitoring

All functionality from the original script is preserved with the same command-line interface.