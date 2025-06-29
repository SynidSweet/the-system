"""
Configuration-driven startup system for The System.

Provides unified configuration for different startup modes while maintaining
process-first principles and systematic validation.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


class StartupMode(Enum):
    """Available startup modes for the system."""
    FULL = "full"           # Complete system with all components
    SIMPLIFIED = "simplified"  # Database + basic API functionality
    MINIMAL = "minimal"     # Basic API only, no database
    DEVELOPMENT = "development"  # Full system with debug features


@dataclass
class DatabaseConfig:
    """Database configuration."""
    enabled: bool = True
    url: str = "sqlite:///data/agent_system.db"
    connect_on_startup: bool = True
    run_migrations: bool = True


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    enable_cors: bool = True
    serve_static: bool = True
    static_path: str = "web/build"


@dataclass
class ComponentConfig:
    """Component initialization configuration."""
    event_system: bool = True
    entity_manager: bool = True
    runtime_engine: bool = True
    tool_system: bool = True
    knowledge_system: bool = True
    websocket_manager: bool = True


@dataclass
class ValidationConfig:
    """System validation configuration."""
    enabled: bool = True
    validate_dependencies: bool = True
    validate_components: bool = True
    validate_configuration: bool = True
    fail_on_validation_error: bool = True


@dataclass
class StartupConfig:
    """Unified startup configuration for all modes."""
    
    mode: StartupMode = StartupMode.FULL
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    components: ComponentConfig = field(default_factory=ComponentConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    
    # Mode-specific configurations
    allowed_file_paths: List[str] = field(default_factory=lambda: ["/code/personal/the-system"])
    debug_mode: bool = False
    step_mode: bool = False
    
    @classmethod
    def for_mode(cls, mode: StartupMode, **overrides) -> "StartupConfig":
        """Create configuration for specific startup mode."""
        
        if mode == StartupMode.MINIMAL:
            return cls(
                mode=mode,
                database=DatabaseConfig(enabled=False),
                api=APIConfig(port=8001),
                components=ComponentConfig(
                    event_system=False,
                    entity_manager=False,
                    runtime_engine=False,
                    tool_system=False,
                    knowledge_system=False,
                    websocket_manager=False
                ),
                validation=ValidationConfig(
                    validate_dependencies=False,
                    validate_components=False
                ),
                **overrides
            )
            
        elif mode == StartupMode.SIMPLIFIED:
            return cls(
                mode=mode,
                api=APIConfig(port=8002),
                components=ComponentConfig(
                    runtime_engine=False,
                    tool_system=False,
                    knowledge_system=False
                ),
                validation=ValidationConfig(
                    validate_components=False
                ),
                **overrides
            )
            
        elif mode == StartupMode.DEVELOPMENT:
            return cls(
                mode=mode,
                debug_mode=True,
                validation=ValidationConfig(
                    enabled=True,
                    fail_on_validation_error=False  # Don't fail in dev mode
                ),
                **overrides
            )
            
        else:  # FULL mode
            return cls(mode=mode, **overrides)
    
    def get_title(self) -> str:
        """Get user-friendly title for this configuration."""
        titles = {
            StartupMode.FULL: "Self-Improving Agent System",
            StartupMode.SIMPLIFIED: "Self-Improving Agent System (Simplified)",
            StartupMode.MINIMAL: "Self-Improving Agent System (Minimal)",
            StartupMode.DEVELOPMENT: "Self-Improving Agent System (Development)"
        }
        return titles.get(self.mode, "Self-Improving Agent System")
    
    def get_description(self) -> str:
        """Get description for this configuration."""
        descriptions = {
            StartupMode.FULL: "Complete process-first recursive agent system",
            StartupMode.SIMPLIFIED: "Simplified startup with database and basic functionality",
            StartupMode.MINIMAL: "Minimal API server without complex initialization",
            StartupMode.DEVELOPMENT: "Full system with development features and debugging"
        }
        return descriptions.get(self.mode, "A process-first recursive agent system")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Port conflicts
        if self.api.port in [8000, 8001, 8002] and self.mode != StartupMode.FULL:
            # Allow port reuse only for appropriate modes
            expected_ports = {
                StartupMode.FULL: 8000,
                StartupMode.MINIMAL: 8001, 
                StartupMode.SIMPLIFIED: 8002
            }
            if self.api.port != expected_ports.get(self.mode):
                issues.append(f"Port {self.api.port} may conflict with other startup modes")
        
        # Component dependencies
        if self.components.runtime_engine and not self.components.entity_manager:
            issues.append("Runtime engine requires entity manager")
            
        if self.components.tool_system and not self.database.enabled:
            issues.append("Tool system requires database")
            
        if self.components.websocket_manager and not self.components.event_system:
            issues.append("WebSocket manager requires event system")
        
        # Static file serving
        if self.api.serve_static:
            static_path = Path(self.api.static_path)
            if not static_path.exists():
                issues.append(f"Static path does not exist: {static_path}")
        
        return issues