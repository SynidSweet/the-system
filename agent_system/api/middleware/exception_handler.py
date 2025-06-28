"""
Centralized exception handling middleware for the Agent System API.

This middleware provides:
- Consistent error response format across all endpoints
- Proper error logging with context
- Custom exception type handling
- Graceful error recovery
"""

import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..exceptions import (
    AgentSystemException,
    EntityNotFoundError,
    ValidationError,
    TaskExecutionError,
    RuntimeError,
    ToolSystemError,
    DatabaseError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle exceptions consistently across all API endpoints."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions that occur."""
        try:
            response = await call_next(request)
            return response
            
        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=404,
                error_type="not_found",
                message=e.message,
                error_code=e.error_code,
                details=e.details
            )
            
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=400,
                error_type="validation_error",
                message=e.message,
                error_code=e.error_code,
                details=e.details
            )
            
        except TaskExecutionError as e:
            logger.error(f"Task execution error: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=422,
                error_type="task_execution_error",
                message=e.message,
                error_code=e.error_code,
                details=e.details
            )
            
        except (RuntimeError, ToolSystemError, DatabaseError) as e:
            logger.error(f"System error: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=503,
                error_type="system_error",
                message="System temporarily unavailable",
                error_code=e.error_code,
                details={"original_message": e.message}
            )
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=500,
                error_type="configuration_error",
                message="System configuration error",
                error_code=e.error_code,
                details={}
            )
            
        except AgentSystemException as e:
            logger.error(f"Agent system error: {e.message}", extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": e.error_code,
                "details": e.details
            })
            return self._create_error_response(
                status_code=500,
                error_type="agent_system_error",
                message=e.message,
                error_code=e.error_code,
                details=e.details
            )
            
        except Exception as e:
            # Log the full traceback for unexpected errors
            logger.exception(f"Unhandled exception: {str(e)}", extra={
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            })
            return self._create_error_response(
                status_code=500,
                error_type="internal_error",
                message="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
                details={}
            )
    
    def _create_error_response(
        self,
        status_code: int,
        error_type: str,
        message: str,
        error_code: str,
        details: Dict[str, Any]
    ) -> JSONResponse:
        """Create a standardized error response."""
        content = {
            "error": {
                "type": error_type,
                "message": message,
                "code": error_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": details
            }
        }
        
        return JSONResponse(
            status_code=status_code,
            content=content
        )