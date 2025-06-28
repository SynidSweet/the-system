#!/usr/bin/env python3
"""
Configuration-driven system seeding for the self-improving agent system.

This refactored script implements clean separation between configuration and execution logic:
1. All configuration moved to YAML files in config/seeds/
2. Modular seeder classes for each entity type
3. Clean, maintainable codebase under 200 lines
4. Comprehensive validation and error handling

This creates the complete foundation for the self-improving system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from ..config.database import DatabaseManager
from scripts.seeders import SystemSeeder, load_configuration

# Create global database instance
database = DatabaseManager()


async def init_database():
    """Initialize database connection and schema"""
    print("🔧 Initializing database...")
    
    try:
        await db_manager.connect()
        print("✅ Database connection established")
        print("✅ Database schema created")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def health_check():
    """Perform comprehensive health check of seeded system"""
    print("🏥 Performing system health check...")
    
    checks_passed = 0
    total_checks = 4
    
    try:
        # Check agents
        agents = await database.agents.list()
        if len(agents) >= 9:
            print(f"  ✅ Found {len(agents)} agents (expected >= 9)")
            checks_passed += 1
        else:
            print(f"  ❌ Found {len(agents)} agents (expected >= 9)")
        
        # Check context documents
        docs = await database.context_documents.list()
        if len(docs) >= 10:
            print(f"  ✅ Found {len(docs)} context documents (expected >= 10)")
            checks_passed += 1
        else:
            print(f"  ❌ Found {len(docs)} context documents (expected >= 10)")
        
        # Check tools
        tools = await database.tools.list()
        if len(tools) >= 10:
            print(f"  ✅ Found {len(tools)} tools (expected >= 10)")
            checks_passed += 1
        else:
            print(f"  ❌ Found {len(tools)} tools (expected >= 10)")
        
        # Check critical agent (process_discovery)
        process_discovery = await database.agents.get_by_name("process_discovery")
        if process_discovery:
            print("  ✅ Process discovery agent found")
            checks_passed += 1
        else:
            print("  ❌ Process discovery agent missing")
        
    except Exception as e:
        print(f"  ❌ Health check error: {e}")
    
    if checks_passed == total_checks:
        print(f"🏥 Health check passed ({checks_passed}/{total_checks})")
        return True
    else:
        print(f"❌ Health check failed ({checks_passed}/{total_checks})")
        return False


async def main():
    """Main seeding function using configuration-driven approach"""
    print("🚀 Seeding Complete Self-Improving Agent System...")
    print("=" * 60)
    print("Configuration-driven seeding with modular architecture")
    print("=" * 60)
    
    # Initialize database
    if not await init_database():
        print("💥 Database initialization failed, aborting")
        return False
    
    # Initialize database manager
    await database.initialize()
    
    # Load and validate configuration
    try:
        config_dir = Path(__file__).parent.parent / "config/seeds"
        print(f"📝 Loading configuration from: {config_dir}")
        
        config = load_configuration(str(config_dir))
        print("✅ Configuration loaded and validated successfully")
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    # Seed all components using configuration
    seeder = SystemSeeder(database, str(config_dir))
    
    if not await seeder.seed_all():
        print("💥 System seeding failed")
        return False
    
    # Health check
    if not await health_check():
        print("💥 Health check failed")
        return False
    
    print("=" * 60)
    print("🎉 Configuration-driven system seeding successful!")
    print("🤖 All agents, context documents, and tools are ready.")
    print("")
    print("System includes:")
    print("  • 9 specialized agents with detailed instructions")
    print("  • Complete documentation from /docs + additional contexts")
    print("  • Core MCP toolkit + system tools")
    print("  • Internal tools (list_agents, list_documents, etc.)")
    print("  • External integrations (git, terminal)")
    print("")
    print("🏗️  Architecture improvements:")
    print("  • Configuration separated from execution logic")
    print("  • Modular seeder classes for maintainability")
    print("  • YAML-based configuration for easy modification")
    print("  • Comprehensive validation and error handling")
    print("")
    print("Ready to submit tasks via:")
    print("  • API: POST http://localhost:8000/tasks")
    print("  • Web UI: http://localhost:8000/app")
    print("  • Manual step mode available for debugging")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)