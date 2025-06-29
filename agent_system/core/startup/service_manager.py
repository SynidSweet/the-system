"""
Service manager for unified startup system.

Handles initialization and shutdown of system components according to 
configuration while following process-first principles.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .startup_config import StartupConfig, StartupMode
from .validation import SystemValidator


logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages system service lifecycle with configuration-driven initialization."""
    
    def __init__(self, config: StartupConfig):
        self.config = config
        self.validator = SystemValidator(config)
        
        # Component instances
        self.database = None
        self.event_integration = None
        self.entity_manager = None
        self.runtime_integration = None
        self.tool_system_manager = None
        
        # State tracking
        self.initialized_components = set()
        self.startup_completed = False
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """FastAPI lifespan context manager."""
        try:
            await self.startup()
            yield
        finally:
            await self.shutdown()
    
    async def startup(self):
        """Execute systematic startup sequence."""
        print(f"🚀 Starting {self.config.get_title()}...")
        print(f"📋 Mode: {self.config.mode.value}")
        
        # Phase 1: Validation (if enabled)
        if self.config.validation.enabled:
            print("🔄 Phase 1: System Validation...")
            validation_result = await self.validator.validate_system()
            
            if not validation_result.is_valid and self.config.validation.fail_on_validation_error:
                raise RuntimeError(f"System validation failed: {validation_result.issues}")
            elif validation_result.issues:
                print(f"⚠️  Validation warnings: {len(validation_result.issues)} issues")
                for issue in validation_result.issues:
                    print(f"   - {issue}")
            
            print("✅ Phase 1: Validation complete")
        
        # Phase 2: Database (if enabled)
        if self.config.database.enabled:
            await self._initialize_database()
        
        # Phase 3: Event System (if enabled)
        if self.config.components.event_system:
            await self._initialize_event_system()
        
        # Phase 4: Entity Manager (if enabled)
        if self.config.components.entity_manager:
            await self._initialize_entity_manager()
        
        # Phase 5: Runtime Engine (if enabled)
        if self.config.components.runtime_engine:
            await self._initialize_runtime_engine()
        
        # Phase 6: Tool System (if enabled)
        if self.config.components.tool_system:
            await self._initialize_tool_system()
        
        # Phase 7: Knowledge System (if enabled)
        if self.config.components.knowledge_system:
            await self._initialize_knowledge_system()
        
        self.startup_completed = True
        print(f"✅ {self.config.get_title()} is ready!")
        print(f"📄 API Documentation: http://localhost:{self.config.api.port}/docs")
        print(f"❤️  Health Check: http://localhost:{self.config.api.port}/health")
    
    async def shutdown(self):
        """Execute systematic shutdown sequence."""
        print(f"🛑 Shutting down {self.config.get_title()}...")
        
        # Shutdown in reverse order
        components_to_shutdown = [
            ("knowledge_system", self._shutdown_knowledge_system),
            ("tool_system", self._shutdown_tool_system),
            ("runtime_engine", self._shutdown_runtime_engine),
            ("entity_manager", self._shutdown_entity_manager),
            ("event_system", self._shutdown_event_system),
            ("database", self._shutdown_database)
        ]
        
        for component_name, shutdown_func in components_to_shutdown:
            if component_name in self.initialized_components:
                try:
                    await shutdown_func()
                except Exception as e:
                    logger.error(f"Error shutting down {component_name}: {e}")
        
        print("✅ Shutdown complete")
    
    # Database initialization
    async def _initialize_database(self):
        """Initialize database component."""
        print("🔄 Phase 2: Database Initialization...")
        
        from ...config.database import DatabaseManager
        self.database = DatabaseManager()
        
        if self.config.database.connect_on_startup:
            await self.database.connect()
        
        self.initialized_components.add("database")
        print("✅ Phase 2: Database initialized")
    
    async def _shutdown_database(self):
        """Shutdown database component."""
        if self.database:
            print("🔄 Shutting down database...")
            await self.database.disconnect()
            print("✅ Database shutdown complete")
    
    # Event system initialization
    async def _initialize_event_system(self):
        """Initialize event system component."""
        print("🔄 Phase 3: Event System Initialization...")
        
        from ...core.event_integration import event_integration
        self.event_integration = event_integration
        await self.event_integration.initialize()
        
        self.initialized_components.add("event_system")
        print("✅ Phase 3: Event system initialized")
    
    async def _shutdown_event_system(self):
        """Shutdown event system component."""
        if self.event_integration:
            print("🔄 Shutting down event system...")
            await self.event_integration.shutdown()
            print("✅ Event system shutdown complete")
    
    # Entity manager initialization
    async def _initialize_entity_manager(self):
        """Initialize entity manager component."""
        print("🔄 Phase 4: Entity Management Layer...")
        
        from ...core.entities.entity_manager import EntityManager
        self.entity_manager = EntityManager(
            self.database.db_url, 
            self.event_integration.event_manager
        )
        
        self.initialized_components.add("entity_manager")
        print("✅ Phase 4: Entity system initialized")
    
    async def _shutdown_entity_manager(self):
        """Shutdown entity manager component."""
        # Entity manager doesn't require explicit shutdown
        print("✅ Entity manager shutdown complete")
    
    # Runtime engine initialization
    async def _initialize_runtime_engine(self):
        """Initialize runtime engine component."""
        print("🔄 Phase 5: Process Framework & Runtime Engine...")
        
        from ...core.runtime.runtime_integration import initialize_runtime_integration
        self.runtime_integration = await initialize_runtime_integration(
            event_manager=self.event_integration.event_manager,
            entity_manager=self.entity_manager,
            mode="runtime_first"
        )
        
        self.initialized_components.add("runtime_engine")
        print("✅ Phase 5: Runtime engine initialized")
    
    async def _shutdown_runtime_engine(self):
        """Shutdown runtime engine component."""
        if self.runtime_integration:
            print("🔄 Shutting down runtime integration...")
            await self.runtime_integration.shutdown()
            print("✅ Runtime integration shutdown complete")
    
    # Tool system initialization
    async def _initialize_tool_system(self):
        """Initialize tool system component."""
        print("🔄 Phase 6: Tool System Initialization...")
        
        from ...tools.mcp_servers.startup import initialize_tool_system
        self.tool_system_manager = await initialize_tool_system(
            db_manager=self.database,
            entity_manager=self.entity_manager,
            config={
                "allowed_file_paths": self.config.allowed_file_paths,
                "github": {},
                "user_interface": {}
            }
        )
        
        # Initialize legacy tools
        from ...tools import initialize_tools
        initialize_tools()
        
        self.initialized_components.add("tool_system")
        print("✅ Phase 6: Tool system initialized")
    
    async def _shutdown_tool_system(self):
        """Shutdown tool system component."""
        if self.tool_system_manager:
            print("🔄 Shutting down tool system...")
            from ...tools.mcp_servers.startup import shutdown_tool_system
            await shutdown_tool_system()
            print("✅ Tool system shutdown complete")
    
    # Knowledge system initialization
    async def _initialize_knowledge_system(self):
        """Initialize knowledge system component."""
        print("🔄 Phase 7: Knowledge System Initialization...")
        
        # Knowledge system is initialized on-demand
        # No explicit initialization required
        
        self.initialized_components.add("knowledge_system")
        print("✅ Phase 7: Knowledge system ready")
    
    async def _shutdown_knowledge_system(self):
        """Shutdown knowledge system component."""
        # Knowledge system doesn't require explicit shutdown
        print("✅ Knowledge system shutdown complete")
    
    # Getters for component access
    def get_database(self):
        """Get database manager instance."""
        return self.database
    
    def get_runtime_integration(self):
        """Get runtime integration instance."""
        return self.runtime_integration
    
    def get_tool_system_manager(self):
        """Get tool system manager instance."""
        return self.tool_system_manager
    
    def get_entity_manager(self):
        """Get entity manager instance."""
        return self.entity_manager
    
    def get_event_integration(self):
        """Get event integration instance."""
        return self.event_integration