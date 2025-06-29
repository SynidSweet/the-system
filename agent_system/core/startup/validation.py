"""
System validation for unified startup.

Provides systematic validation of framework components before initialization,
following process-first principles.
"""

import sys
import importlib
from typing import List, Dict, Any, NamedTuple
from pathlib import Path

from .startup_config import StartupConfig


class ValidationResult(NamedTuple):
    """Result of system validation."""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    component_status: Dict[str, bool]


class SystemValidator:
    """Validates system components and dependencies before startup."""
    
    def __init__(self, config: StartupConfig):
        self.config = config
    
    async def validate_system(self) -> ValidationResult:
        """Execute comprehensive system validation."""
        issues = []
        warnings = []
        component_status = {}
        
        # Configuration validation
        config_issues = self.config.validate()
        issues.extend(config_issues)
        
        # Dependency validation
        if self.config.validation.validate_dependencies:
            dep_issues, dep_warnings = self._validate_dependencies()
            issues.extend(dep_issues)
            warnings.extend(dep_warnings)
        
        # Component validation
        if self.config.validation.validate_components:
            comp_issues, comp_warnings, comp_status = self._validate_components()
            issues.extend(comp_issues)
            warnings.extend(comp_warnings)
            component_status.update(comp_status)
        
        # File system validation
        fs_issues, fs_warnings = self._validate_filesystem()
        issues.extend(fs_issues)
        warnings.extend(fs_warnings)
        
        is_valid = len(issues) == 0
        return ValidationResult(is_valid, issues, warnings, component_status)
    
    def _validate_dependencies(self) -> tuple[List[str], List[str]]:
        """Validate Python dependencies and imports."""
        issues = []
        warnings = []
        
        # Critical dependencies
        critical_deps = [
            "fastapi",
            "uvicorn", 
            "pydantic",
            "sqlmodel"
        ]
        
        for dep in critical_deps:
            try:
                importlib.import_module(dep)
            except ImportError:
                issues.append(f"Critical dependency missing: {dep}")
        
        # Optional dependencies based on configuration
        if self.config.database.enabled:
            try:
                importlib.import_module("sqlite3")
            except ImportError:
                issues.append("Database enabled but sqlite3 not available")
        
        if self.config.components.websocket_manager:
            try:
                importlib.import_module("websockets")
            except ImportError:
                warnings.append("WebSocket support may be limited")
        
        return issues, warnings
    
    def _validate_components(self) -> tuple[List[str], List[str], Dict[str, bool]]:
        """Validate system components can be imported."""
        issues = []
        warnings = []
        status = {}
        
        # Core components
        core_components = [
            ("config.database", "DatabaseManager"),
            ("core.entities.entity_manager", "EntityManager"),
            ("api.main", "app")
        ]
        
        for module_path, component_name in core_components:
            try:
                module = importlib.import_module(f"agent_system.{module_path}")
                if hasattr(module, component_name):
                    status[f"{module_path}.{component_name}"] = True
                else:
                    status[f"{module_path}.{component_name}"] = False
                    warnings.append(f"Component {component_name} not found in {module_path}")
            except ImportError as e:
                status[f"{module_path}.{component_name}"] = False
                issues.append(f"Cannot import {module_path}: {e}")
        
        # Optional components based on configuration
        if self.config.components.event_system:
            try:
                importlib.import_module("agent_system.core.event_integration")
                status["event_system"] = True
            except ImportError:
                status["event_system"] = False
                issues.append("Event system enabled but cannot import event_integration")
        
        if self.config.components.runtime_engine:
            try:
                importlib.import_module("agent_system.core.runtime.runtime_integration")
                status["runtime_engine"] = True
            except ImportError:
                status["runtime_engine"] = False
                issues.append("Runtime engine enabled but cannot import runtime_integration")
        
        if self.config.components.tool_system:
            try:
                importlib.import_module("agent_system.tools.mcp_servers.startup")
                status["tool_system"] = True
            except ImportError:
                status["tool_system"] = False
                issues.append("Tool system enabled but cannot import tool startup")
        
        return issues, warnings, status
    
    def _validate_filesystem(self) -> tuple[List[str], List[str]]:
        """Validate filesystem requirements."""
        issues = []
        warnings = []
        
        # Check database directory
        if self.config.database.enabled:
            db_url = self.config.database.url
            if db_url.startswith("sqlite:///"):
                db_path = Path(db_url.replace("sqlite:///", ""))
                db_dir = db_path.parent
                if not db_dir.exists():
                    try:
                        db_dir.mkdir(parents=True)
                    except Exception:
                        issues.append(f"Cannot create database directory: {db_dir}")
        
        # Check static files directory
        if self.config.api.serve_static:
            static_path = Path(self.config.api.static_path)
            if not static_path.exists():
                warnings.append(f"Static files directory not found: {static_path}")
        
        # Check allowed file paths
        for path_str in self.config.allowed_file_paths:
            path = Path(path_str)
            if not path.exists():
                warnings.append(f"Allowed file path does not exist: {path}")
            elif not path.is_dir():
                warnings.append(f"Allowed file path is not a directory: {path}")
        
        return issues, warnings
    
    def _check_port_availability(self) -> List[str]:
        """Check if the configured port is available."""
        issues = []
        
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex((self.config.api.host, self.config.api.port))
                if result == 0:
                    issues.append(f"Port {self.config.api.port} is already in use")
        except Exception:
            # If we can't check, assume it's fine
            pass
        
        return issues