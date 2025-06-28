"""
Main test runner for the agent system.

Orchestrates all test suites and generates comprehensive reports.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.database import db_manager
from config.database import DatabaseManager
from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import register_core_tools
from tools.system_tools.mcp_integrations import register_system_tools
from tools.system_tools.internal_tools import register_internal_tools
from core.entities.entity_manager import EntityManager
from core.runtime.runtime_engine import RuntimeEngine

from .test_utils import TestReporter
from .health_tests import HealthTests
from .functional_tests import FunctionalTests
from .performance_tests import PerformanceTests
from .integration_tests import IntegrationTests


class SystemTestRunner:
    """Orchestrates system test execution"""
    
    def __init__(self):
        self.reporter = TestReporter()
        self.database = None
        self.entity_manager = None
        self.runtime_engine = None
        
    async def initialize(self) -> None:
        """Initialize test dependencies"""
        print("🚀 Initializing test environment...")
        
        # Initialize database
        await db_manager.connect()
        self.database = DatabaseManager()
        await self.database.initialize()
        
        # Initialize entity manager
        db_path = Path(__file__).parent.parent.parent / "data" / "agent_system.db"
        self.entity_manager = EntityManager(str(db_path))
        await self.entity_manager.initialize()
        
        # Initialize runtime engine
        self.runtime_engine = RuntimeEngine(self.entity_manager)
        
        # Register all tools
        register_core_tools()
        register_system_tools()
        register_internal_tools()
        
        print("✅ Test environment initialized\n")
    
    async def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🧪 Running Comprehensive System Tests")
        print("=" * 60)
        
        await self.initialize()
        
        # Define test suites
        suites = [
            ("health", HealthTests(self.database, tool_registry)),
            ("functional", FunctionalTests(self.database, tool_registry, self.entity_manager)),
            ("performance", PerformanceTests(self.database, self.entity_manager)),
            ("integration", IntegrationTests(self.database, self.entity_manager, self.runtime_engine))
        ]
        
        overall_success = True
        
        # Run each suite
        for suite_name, suite_instance in suites:
            print(f"\n🔍 Running {suite_name.upper()} tests...")
            try:
                suite_results = await suite_instance.run_all()
                self.reporter.add_suite_results(suite_results)
                suite_results.print_summary()
                
                if suite_results.failed > 0:
                    overall_success = False
                    
            except Exception as e:
                print(f"❌ {suite_name.upper()} suite failed with error: {str(e)}")
                overall_success = False
        
        # Generate and display final report
        self.reporter.print_summary()
        
        # Save detailed report
        await self._save_report()
        
        return overall_success
    
    async def run_suite(self, suite_name: str) -> bool:
        """Run a specific test suite"""
        print(f"🧪 Running {suite_name.upper()} Test Suite")
        print("=" * 60)
        
        await self.initialize()
        
        # Map suite names to classes
        suite_map = {
            "health": HealthTests(self.database, tool_registry),
            "functional": FunctionalTests(self.database, tool_registry, self.entity_manager),
            "performance": PerformanceTests(self.database, self.entity_manager),
            "integration": IntegrationTests(self.database, self.entity_manager, self.runtime_engine)
        }
        
        if suite_name not in suite_map:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(suite_map.keys())}")
            return False
        
        # Run selected suite
        suite_instance = suite_map[suite_name]
        try:
            suite_results = await suite_instance.run_all()
            self.reporter.add_suite_results(suite_results)
            suite_results.print_summary()
            
            # Generate report
            self.reporter.print_summary()
            await self._save_report()
            
            return suite_results.failed == 0
            
        except Exception as e:
            print(f"❌ {suite_name.upper()} suite failed with error: {str(e)}")
            return False
    
    async def _save_report(self) -> None:
        """Save detailed test report to file"""
        report = self.reporter.generate_report()
        
        # Create reports directory
        reports_dir = Path(__file__).parent.parent.parent / "test_reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = report["timestamp"].replace(":", "-").replace(".", "-")
        filename = reports_dir / f"test_report_{timestamp}.json"
        
        # Save report
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")
    
    async def cleanup(self) -> None:
        """Clean up test resources"""
        if self.database:
            # Close database connections
            pass


async def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(
        description="System testing framework for the agent system"
    )
    parser.add_argument(
        "--suite",
        choices=["health", "functional", "performance", "integration"],
        help="Run specific test suite only"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = SystemTestRunner()
    
    try:
        if args.suite:
            success = await runner.run_suite(args.suite)
        else:
            success = await runner.run_all_tests()
        
        # Cleanup
        await runner.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())