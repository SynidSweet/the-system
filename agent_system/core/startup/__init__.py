"""
Unified startup system for The System.

This module provides configuration-driven startup with systematic validation
following process-first principles.
"""

from .startup_config import StartupConfig, StartupMode
from .service_manager import ServiceManager
from .validation import SystemValidator

__all__ = [
    "StartupConfig",
    "StartupMode", 
    "ServiceManager",
    "SystemValidator"
]