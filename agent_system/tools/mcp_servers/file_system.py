"""
File System MCP Server - Provides sandboxed file operations.

This server implements secure file operations with path restrictions:
- Read files within allowed directories
- Write files with safety checks
- List directory contents
- Create/delete files with permissions
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent_system.tools.mcp_servers.base import MCPServer
from agent_system.core.permissions.manager import DatabasePermissionManager


class FileSystemMCPServer(MCPServer):
    """
    MCP server for file system operations with sandboxing.
    
    Operations:
    - read_file: Read file contents
    - write_file: Write content to file
    - list_directory: List directory contents
    - create_directory: Create new directory
    - delete_file: Delete a file
    - copy_file: Copy file to new location
    - move_file: Move file to new location
    - get_file_info: Get file metadata
    """
    
    def __init__(
        self,
        permission_manager: DatabasePermissionManager,
        allowed_paths: List[str]
    ):
        super().__init__(permission_manager)
        
        # Convert to absolute paths and validate
        self.allowed_paths = []
        for path in allowed_paths:
            abs_path = Path(path).resolve()
            if abs_path.exists():
                self.allowed_paths.append(abs_path)
            else:
                print(f"Warning: Allowed path does not exist: {path}")
        
        if not self.allowed_paths:
            raise ValueError("No valid allowed paths configured")
        
        # Operation permissions
        self.read_operations = {"read_file", "list_directory", "get_file_info"}
        self.write_operations = {"write_file", "create_directory", "delete_file", 
                                "copy_file", "move_file"}
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is within allowed directories."""
        try:
            target_path = Path(path).resolve()
            
            # Check if path is under any allowed directory
            for allowed_path in self.allowed_paths:
                try:
                    target_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def _validate_path(self, path: str, operation: str) -> Path:
        """Validate and resolve a path for an operation."""
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Resolve to absolute path
        abs_path = Path(path).resolve()
        
        # Check if path is allowed
        if not self._is_path_allowed(str(abs_path)):
            raise PermissionError(
                f"Access denied: Path '{path}' is outside allowed directories"
            )
        
        # For write operations, check parent directory exists
        if operation in self.write_operations and operation != "create_directory":
            if not abs_path.parent.exists():
                raise ValueError(f"Parent directory does not exist: {abs_path.parent}")
        
        return abs_path
    
    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Read contents of a file."""
        # Validate path
        path = self._validate_path(file_path, "read_file")
        
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }
        
        try:
            # Read file content
            if encoding:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            else:
                with open(path, 'rb') as f:
                    content = f.read()
                    # Return base64 for binary files
                    import base64
                    content = base64.b64encode(content).decode('ascii')
            
            return {
                "success": True,
                "content": content,
                "encoding": encoding,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
    
    async def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Write content to a file."""
        # Validate path
        path = self._validate_path(file_path, "write_file")
        
        try:
            # Create parent directories if requested
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            if encoding:
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content)
            else:
                # Assume base64 encoded binary
                import base64
                with open(path, 'wb') as f:
                    f.write(base64.b64decode(content))
            
            return {
                "success": True,
                "file_path": str(path),
                "size": len(content),
                "created": not path.exists(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}"
            }
    
    async def list_directory(
        self,
        directory_path: str,
        pattern: str = "*",
        recursive: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """List contents of a directory."""
        # Validate path
        path = self._validate_path(directory_path, "list_directory")
        
        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}"
            }
        
        if not path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {directory_path}"
            }
        
        try:
            items = []
            
            if recursive:
                # Recursive listing
                for item_path in path.rglob(pattern):
                    items.append(self._get_file_info(item_path))
            else:
                # Non-recursive listing
                for item_path in path.glob(pattern):
                    items.append(self._get_file_info(item_path))
            
            return {
                "success": True,
                "directory": str(path),
                "items": items,
                "count": len(items)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list directory: {str(e)}"
            }
    
    async def create_directory(
        self,
        directory_path: str,
        create_parents: bool = True,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Create a new directory."""
        # Validate path
        path = self._validate_path(directory_path, "create_directory")
        
        if path.exists():
            return {
                "success": False,
                "error": f"Path already exists: {directory_path}"
            }
        
        try:
            path.mkdir(parents=create_parents, exist_ok=False)
            
            return {
                "success": True,
                "directory_path": str(path),
                "created": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create directory: {str(e)}"
            }
    
    async def delete_file(
        self,
        file_path: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Delete a file (not directories)."""
        # Validate path
        path = self._validate_path(file_path, "delete_file")
        
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }
        
        try:
            # Store file info before deletion
            file_info = self._get_file_info(path)
            
            # Delete the file
            path.unlink()
            
            return {
                "success": True,
                "deleted_file": str(path),
                "file_info": file_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete file: {str(e)}"
            }
    
    async def copy_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Copy a file to a new location."""
        # Validate paths
        src_path = self._validate_path(source_path, "copy_file")
        dst_path = self._validate_path(destination_path, "copy_file")
        
        if not src_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {source_path}"
            }
        
        if not src_path.is_file():
            return {
                "success": False,
                "error": f"Source is not a file: {source_path}"
            }
        
        if dst_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Destination already exists: {destination_path}"
            }
        
        try:
            # Copy the file
            shutil.copy2(src_path, dst_path)
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path),
                "size": src_path.stat().st_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to copy file: {str(e)}"
            }
    
    async def move_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Move a file to a new location."""
        # Validate paths
        src_path = self._validate_path(source_path, "move_file")
        dst_path = self._validate_path(destination_path, "move_file")
        
        if not src_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {source_path}"
            }
        
        if not src_path.is_file():
            return {
                "success": False,
                "error": f"Source is not a file: {source_path}"
            }
        
        if dst_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Destination already exists: {destination_path}"
            }
        
        try:
            # Move the file
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to move file: {str(e)}"
            }
    
    async def get_file_info(
        self,
        file_path: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get detailed information about a file or directory."""
        # Validate path
        path = self._validate_path(file_path, "get_file_info")
        
        if not path.exists():
            return {
                "success": False,
                "error": f"Path not found: {file_path}"
            }
        
        try:
            info = self._get_file_info(path)
            
            return {
                "success": True,
                "file_info": info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get file info: {str(e)}"
            }
    
    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get file/directory information."""
        stat = path.stat()
        
        return {
            "path": str(path),
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size if path.is_file() else None,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "permissions": oct(stat.st_mode)[-3:],
            "is_symlink": path.is_symlink(),
            "exists": path.exists()
        }
    
    @property
    def name(self) -> str:
        """Return the server name."""
        return "file_system"
    
    @property 
    def supported_operations(self) -> List[str]:
        """Return list of supported operations."""
        return [
            "read_file",
            "write_file", 
            "list_directory",
            "create_directory",
            "delete_file",
            "copy_file",
            "move_file",
            "get_file_info"
        ]