"""Application startup and shutdown lifecycle management."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from ..config.database import DatabaseManager
from ..core.event_integration import event_integration
from ..core.runtime.runtime_integration import initialize_runtime_integration, RuntimeIntegration


logger = logging.getLogger(__name__)

# Global instances
runtime_integration: Optional[RuntimeIntegration] = None
tool_system_manager = None


def get_runtime_integration() -> Optional[RuntimeIntegration]:
    """Get the global runtime integration instance."""
    return runtime_integration


def get_tool_system_manager():
    """Get the global tool system manager."""
    return tool_system_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with startup and shutdown logic."""
    # Startup
    try:
        await startup_sequence()
        yield
    finally:
        # Shutdown
        await shutdown_sequence()


async def startup_sequence():
    """Execute the complete startup sequence for the application."""
    global runtime_integration, tool_system_manager
    
    print("🚀 Starting Agent System API...")
    
    # Get database instance
    database = get_database()
    
    # Initialize database
    print("🔄 Initializing Database...")
    await database.connect()
    print("✅ Database initialized")
    
    # Initialize event system integration
    print("🔄 Initializing Event System...")
    await event_integration.initialize()
    print("✅ Event system initialized")
    
    # Initialize entity system (Phase 3)
    print("🔄 Initializing Entity Management Layer...")
    from core.entities.entity_manager import EntityManager
    entity_manager = EntityManager(database.db_url, event_integration.event_manager)
    print("✅ Entity system initialized")
    
    # Initialize runtime system (Phase 4)
    print("🔄 Initializing Process Framework & Runtime Engine...")
    runtime_integration = await initialize_runtime_integration(
        event_manager=event_integration.event_manager,
        entity_manager=entity_manager,
        mode="runtime_first"  # Force runtime-only mode
    )
    print("✅ Runtime engine initialized with process framework (runtime-only mode)")
    
    # Initialize tool system (Phase 5)
    print("🔄 Initializing Optional Tooling System...")
    from tools.mcp_servers.startup import initialize_tool_system
    tool_system_manager = await initialize_tool_system(
        db_manager=database,
        entity_manager=entity_manager,
        config={
            "allowed_file_paths": ["/code/personal/the-system"],
            "github": {},
            "user_interface": {}
        }
    )
    print("✅ Tool system initialized with MCP servers")
    
    # Initialize and register legacy tools
    print("🔄 Initializing Legacy Tools...")
    from tools import initialize_tools
    initialize_tools()
    print("✅ Legacy tools initialized")
    
    # Self-improvement engine removed in Phase 8 cleanup
    # Functionality integrated into entity framework and event system
    
    # No need to start old task manager - runtime engine handles everything
    
    print("✅ Agent System API is ready!")


async def shutdown_sequence():
    """Execute the complete shutdown sequence for the application."""
    global runtime_integration, tool_system_manager
    
    print("🛑 Shutting down Agent System API...")
    
    # Shutdown tool system
    if tool_system_manager:
        print("🔄 Shutting down tool system...")
        try:
            from tools.mcp_servers.startup import shutdown_tool_system
            await shutdown_tool_system()
            print("✅ Tool system shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down tool system: {e}")
    
    # Shutdown runtime
    if runtime_integration:
        print("🔄 Shutting down runtime integration...")
        try:
            await runtime_integration.shutdown()
            runtime_integration = None
            print("✅ Runtime integration shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down runtime integration: {e}")
    
    # Shutdown event system
    try:
        print("🔄 Shutting down event system...")
        await event_integration.shutdown()
        print("✅ Event system shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down event system: {e}")
    
    # Shutdown database
    try:
        print("🔄 Shutting down database...")
        database = get_database()
        await database.disconnect()
        print("✅ Database shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down database: {e}")
    
    print("✅ Shutdown complete")


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    # Import here to avoid circular imports
    from .main import database
    return database