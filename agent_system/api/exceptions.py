"""
Custom exception types for the Agent System API.

This module defines domain-specific exceptions that provide better error handling
and more informative responses to API clients.
"""

from typing import Optional, Dict, Any


class AgentSystemException(Exception):
    """Base exception for all Agent System errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)


class EntityNotFoundError(AgentSystemException):
    """Raised when a requested entity cannot be found."""
    pass


class ValidationError(AgentSystemException):
    """Raised when request data fails validation."""
    pass


class TaskExecutionError(AgentSystemException):
    """Raised when task execution fails."""
    pass


class RuntimeError(AgentSystemException):
    """Raised when runtime system encounters errors."""
    pass


class ToolSystemError(AgentSystemException):
    """Raised when tool system operations fail."""
    pass


class DatabaseError(AgentSystemException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AgentSystemException):
    """Raised when system configuration is invalid."""
    pass