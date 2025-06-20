"""
Event System Integration - Enables parallel operation with existing message system
"""
import asyncio
from typing import Optional
from functools import wraps

from .events import event_manager
from .universal_agent_runtime import UniversalAgentRuntime
from config.settings import settings


class EventSystemIntegration:
    """Manages the integration and parallel operation of event system"""
    
    def __init__(self):
        self.event_system_enabled = True
        self.flush_task: Optional[asyncio.Task] = None
        self.event_manager = event_manager
        
    async def initialize(self):
        """Initialize event system integration"""
        if self.event_system_enabled:
            # Start periodic event flush task
            self.flush_task = asyncio.create_task(self._periodic_flush())
            print("Event system integration initialized")
    
    async def shutdown(self):
        """Shutdown event system integration"""
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush of any remaining events
        await event_manager.flush()
        print("Event system integration shut down")
    
    async def _periodic_flush(self):
        """Periodically flush events to database"""
        while True:
            try:
                await asyncio.sleep(10)  # Flush every 10 seconds
                await event_manager.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in periodic event flush: {e}")
    
    def get_agent_class(self):
        """Get the appropriate agent class based on configuration"""
        # Always return the runtime agent now
        return UniversalAgentRuntime
    
    def is_event_system_active(self) -> bool:
        """Check if event system is currently active"""
        return self.event_system_enabled


# Global integration instance
event_integration = EventSystemIntegration()


def with_event_tracking(event_type_start, event_type_end, entity_type):
    """Decorator to add event tracking to any async function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not event_integration.is_event_system_active():
                return await func(self, *args, **kwargs)
            
            # Determine entity_id from self or args
            entity_id = getattr(self, 'id', None) or getattr(self, 'task_id', 0)
            
            # Log start event
            start_event_id = await event_manager.log_event(
                event_type_start,
                entity_type,
                entity_id,
                event_data={
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
            )
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Execute function
                result = await func(self, *args, **kwargs)
                
                # Log end event
                await event_manager.log_event(
                    event_type_end,
                    entity_type,
                    entity_id,
                    event_data={
                        'function': func.__name__,
                        'success': True
                    },
                    outcome=EventOutcome.SUCCESS,
                    duration_seconds=asyncio.get_event_loop().time() - start_time,
                    parent_event_id=start_event_id
                )
                
                return result
                
            except Exception as e:
                # Log error event
                await event_manager.log_event(
                    EventType.SYSTEM_ERROR,
                    entity_type,
                    entity_id,
                    event_data={
                        'function': func.__name__,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    outcome=EventOutcome.ERROR,
                    duration_seconds=asyncio.get_event_loop().time() - start_time,
                    parent_event_id=start_event_id
                )
                raise
        
        return wrapper
    return decorator


# Import guards to prevent circular imports
from .events import EventType, EventOutcome


# Configuration helpers
def enable_event_system():
    """Enable the event system"""
    event_integration.event_system_enabled = True
    print("Event system enabled")


def disable_event_system():
    """Disable the event system (for testing or rollback)"""
    event_integration.event_system_enabled = False
    print("Event system disabled")


def use_enhanced_agents(enabled: bool = True):
    """Enable or disable enhanced agents with event tracking"""
    event_integration.use_enhanced_agent = enabled
    print(f"Enhanced agents {'enabled' if enabled else 'disabled'}")