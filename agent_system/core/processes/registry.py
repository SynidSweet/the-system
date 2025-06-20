"""Process registry for managing and loading processes."""

import importlib
import inspect
from typing import Dict, Type, Optional, List, Any
from pathlib import Path
import logging

from agent_system.core.processes.base import BaseProcess
from agent_system.core.entities.entity_manager import EntityManager
from agent_system.core.events.event_manager import EventManager


logger = logging.getLogger(__name__)


class ProcessRegistry:
    """Registry for managing process implementations."""
    
    def __init__(
        self,
        entity_manager: EntityManager,
        event_manager: EventManager
    ):
        self.entity_manager = entity_manager
        self.event_manager = event_manager
        
        # Registry of process classes
        self.processes: Dict[str, Type[BaseProcess]] = {}
        
        # Process metadata
        self.process_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Default processes
        self._register_default_processes()
    
    def _register_default_processes(self):
        """Register default system processes."""
        # Map of process names to their module paths
        default_processes = {
            "neutral_task": "agent_system.core.processes.neutral_task_process",
            "break_down_task_process": "agent_system.core.processes.tool_processes.break_down_task",
            "create_subtask_process": "agent_system.core.processes.tool_processes.create_subtask",
            "end_task_process": "agent_system.core.processes.tool_processes.end_task",
            "need_more_context_process": "agent_system.core.processes.tool_processes.need_more_context",
            "need_more_tools_process": "agent_system.core.processes.tool_processes.need_more_tools",
            "flag_for_review_process": "agent_system.core.processes.tool_processes.flag_for_review",
        }
        
        for process_name, module_path in default_processes.items():
            try:
                self._load_process_from_module(process_name, module_path)
            except Exception as e:
                logger.warning(f"Could not load default process {process_name}: {e}")
    
    def _load_process_from_module(self, process_name: str, module_path: str):
        """Load a process class from a module."""
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find the process class
            process_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseProcess) and 
                    obj != BaseProcess):
                    process_class = obj
                    break
            
            if process_class:
                self.register_process(process_name, process_class)
                logger.debug(f"Loaded process {process_name} from {module_path}")
            else:
                logger.warning(f"No process class found in {module_path}")
                
        except Exception as e:
            logger.error(f"Error loading process from {module_path}: {e}")
            raise
    
    def register_process(
        self,
        name: str,
        process_class: Type[BaseProcess],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a process class."""
        if not issubclass(process_class, BaseProcess):
            raise ValueError(f"Process class must inherit from BaseProcess")
        
        self.processes[name] = process_class
        self.process_metadata[name] = metadata or {}
        
        logger.info(f"Registered process: {name}")
    
    def unregister_process(self, name: str) -> bool:
        """Unregister a process."""
        if name in self.processes:
            del self.processes[name]
            del self.process_metadata[name]
            logger.info(f"Unregistered process: {name}")
            return True
        return False
    
    def get_process_class(self, name: str) -> Optional[Type[BaseProcess]]:
        """Get a process class by name."""
        return self.processes.get(name)
    
    def create_process(self, name: str) -> Optional[BaseProcess]:
        """Create a process instance by name."""
        process_class = self.get_process_class(name)
        if process_class:
            return process_class(self.entity_manager, self.event_manager)
        return None
    
    async def execute_process(
        self,
        name: str,
        **kwargs
    ) -> Any:
        """Execute a process by name."""
        process = self.create_process(name)
        if not process:
            raise ValueError(f"Process {name} not found in registry")
        
        # Validate parameters
        if not await process.validate_parameters(**kwargs):
            raise ValueError(f"Invalid parameters for process {name}")
        
        # Log start
        await process.log_start(**kwargs)
        
        try:
            # Execute the process
            result = await process.execute(**kwargs)
            
            # Log completion
            await process.log_completion(result)
            
            return result
            
        except Exception as e:
            # Handle error
            return await process.handle_error(e, **kwargs)
    
    def list_processes(self) -> List[Dict[str, Any]]:
        """List all registered processes."""
        return [
            {
                "name": name,
                "class": process_class.__name__,
                "module": process_class.__module__,
                "can_rollback": getattr(process_class, 'can_rollback', False),
                "metadata": self.process_metadata.get(name, {})
            }
            for name, process_class in self.processes.items()
        ]
    
    def get_process_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a process."""
        if name not in self.processes:
            return {}
        
        process_class = self.processes[name]
        return {
            "name": name,
            "class": process_class.__name__,
            "module": process_class.__module__,
            "docstring": inspect.getdoc(process_class),
            "can_rollback": getattr(process_class, 'can_rollback', False),
            "parameters": self._get_process_parameters(process_class),
            "custom_metadata": self.process_metadata.get(name, {})
        }
    
    def _get_process_parameters(self, process_class: Type[BaseProcess]) -> Dict[str, Any]:
        """Extract parameter information from process execute method."""
        try:
            execute_method = process_class.execute
            signature = inspect.signature(execute_method)
            
            parameters = {}
            for param_name, param in signature.parameters.items():
                if param_name in ['self', 'kwargs']:
                    continue
                
                param_info = {
                    "type": str(param.annotation) if param.annotation != param.empty else "Any",
                    "required": param.default == param.empty,
                    "default": param.default if param.default != param.empty else None
                }
                parameters[param_name] = param_info
            
            return parameters
            
        except Exception as e:
            logger.warning(f"Could not extract parameters: {e}")
            return {}
    
    def load_processes_from_directory(self, directory: Path):
        """Load all process modules from a directory."""
        if not directory.exists():
            logger.warning(f"Process directory does not exist: {directory}")
            return
        
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = file_path.stem
            process_name = module_name.replace("_process", "")
            
            try:
                # Convert file path to module path
                module_path = str(file_path).replace("/", ".").replace(".py", "")
                if "agent_system" in module_path:
                    module_path = module_path[module_path.index("agent_system"):]
                
                self._load_process_from_module(process_name, module_path)
                
            except Exception as e:
                logger.error(f"Error loading process from {file_path}: {e}")
    
    def reload_process(self, name: str) -> bool:
        """Reload a process module."""
        if name not in self.processes:
            return False
        
        process_class = self.processes[name]
        module = inspect.getmodule(process_class)
        
        try:
            # Reload the module
            importlib.reload(module)
            
            # Re-register the process
            self._load_process_from_module(name, module.__name__)
            return True
            
        except Exception as e:
            logger.error(f"Error reloading process {name}: {e}")
            return False


# Global process registry instance
_process_registry: Optional[ProcessRegistry] = None


def get_process_registry() -> Optional[ProcessRegistry]:
    """Get the global process registry instance."""
    return _process_registry


def initialize_process_registry(
    entity_manager: EntityManager,
    event_manager: EventManager
) -> ProcessRegistry:
    """Initialize the global process registry."""
    global _process_registry
    _process_registry = ProcessRegistry(entity_manager, event_manager)
    return _process_registry