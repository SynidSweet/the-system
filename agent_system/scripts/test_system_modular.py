#!/usr/bin/env python3
"""
Modular system testing script - uses the new modular test architecture.

This script provides a backwards-compatible interface to the new modular test system.
It maintains the same command-line interface as the original test_system.py.

Usage:
    python scripts/test_system_modular.py                    # Run all tests
    python scripts/test_system_modular.py --suite health     # Run health tests only
    python scripts/test_system_modular.py --suite functional # Run functional tests only
    python scripts/test_system_modular.py --suite performance # Run performance tests only
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path to import test modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.system.test_runner import main


if __name__ == "__main__":
    # Use the test runner's main function directly
    asyncio.run(main())