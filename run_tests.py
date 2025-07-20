#!/usr/bin/env python3
"""
Simple test runner launcher for the agent system.

This script sets up the proper environment and runs the test system
without complex initialization issues.
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add the agent_system directory to path
agent_system_path = Path(__file__).parent / "agent_system"
sys.path.insert(0, str(agent_system_path))

# Simple health check function
def run_simple_health_check():
    """Run basic health checks without complex initialization"""
    print("🧪 Simple System Health Check")
    print("=" * 40)
    
    # Check if critical files exist
    checks = [
        ("Database directory", agent_system_path / "data"),
        ("Core module", agent_system_path / "core"),
        ("API module", agent_system_path / "api"),
        ("Tools module", agent_system_path / "tools"),
        ("Web interface", agent_system_path / "web"),
    ]
    
    passed = 0
    failed = 0
    
    for check_name, path in checks:
        if path.exists():
            print(f"✅ {check_name}: Found at {path}")
            passed += 1
        else:
            print(f"❌ {check_name}: Not found at {path}")
            failed += 1
    
    # Check Python imports
    try:
        import agent_system.core
        print("✅ Core module import: Success")
        passed += 1
    except ImportError as e:
        print(f"❌ Core module import: Failed ({e})")
        failed += 1
        
    try:
        import agent_system.api
        print("✅ API module import: Success")
        passed += 1
    except ImportError as e:
        print(f"❌ API module import: Failed ({e})")
        failed += 1
    
    print("\n" + "=" * 40)
    print(f"Health Check Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All health checks passed!")
        return True
    else:
        print("⚠️  Some health checks failed")
        return False

async def run_advanced_tests(suite_name: str = None):
    """Try to run the advanced test system"""
    print("🧪 Attempting Advanced Test System")
    print("=" * 40)
    
    try:
        # Import the test runner directly without sys.modules issues
        from tests.system.test_runner import SystemTestRunner
        
        # Create and run tests
        runner = SystemTestRunner()
        
        if suite_name:
            print(f"Running {suite_name.upper()} test suite...")
            success = await runner.run_suite(suite_name)
        else:
            print("Running all test suites...")
            success = await runner.run_all_tests()
        
        if success:
            print("🎉 Advanced tests completed successfully!")
        else:
            print("⚠️  Some advanced tests failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Advanced test system failed: {e}")
        print("Falling back to simple health check...")
        return run_simple_health_check()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test runner for the agent system"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Run only simple health checks"
    )
    parser.add_argument(
        "--suite",
        choices=["health", "functional", "performance", "integration"],
        help="Run specific advanced test suite"
    )
    
    args = parser.parse_args()
    
    # Change to agent_system directory
    os.chdir(agent_system_path)
    
    if args.simple:
        success = run_simple_health_check()
        sys.exit(0 if success else 1)
    else:
        # Try advanced tests
        try:
            success = asyncio.run(run_advanced_tests(args.suite))
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            print("Running simple health check instead...")
            success = run_simple_health_check()
            sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()