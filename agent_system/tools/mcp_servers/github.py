"""
GitHub MCP Server - Provides version control operations via git.

This server implements secure git operations with:
- Repository path restrictions  
- Safe command execution
- Branch protection
- Commit message validation
"""

import os
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from agent_system.tools.mcp_servers.base import MCPServer
from agent_system.core.permissions.manager import DatabasePermissionManager


class GitHubMCPServer(MCPServer):
    """
    MCP server for GitHub/git operations with security controls.
    
    Operations:
    - get_status: Get current repository status
    - commit_changes: Create a commit with staged changes
    - stage_files: Stage files for commit
    - unstage_files: Unstage files
    - get_log: Get commit history
    - get_diff: Get differences (staged/unstaged)
    - create_branch: Create a new branch
    - switch_branch: Switch to a different branch
    - list_branches: List all branches
    - pull_changes: Pull from remote
    - push_changes: Push to remote (with restrictions)
    """
    
    def __init__(
        self,
        permission_manager: DatabasePermissionManager,
        repo_path: str,
        allow_push: bool = False,
        protected_branches: Optional[List[str]] = None
    ):
        super().__init__(permission_manager)
        
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path not found: {repo_path}")
        
        # Verify it's a git repository
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {repo_path}")
        
        self.allow_push = allow_push
        self.protected_branches = protected_branches or ["main", "master", "production"]
    
    async def _run_git_command(
        self,
        args: List[str],
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """Run a git command and return the result."""
        cmd = ["git"] + args
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path)
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_status(
        self,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get current repository status."""
        result = await self._run_git_command(["status", "--porcelain"])
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", result.get("stderr"))
            }
        
        # Parse status output
        status_lines = result["stdout"].strip().split('\n') if result["stdout"] else []
        
        staged = []
        unstaged = []
        untracked = []
        
        for line in status_lines:
            if not line:
                continue
            
            status = line[:2]
            filename = line[3:]
            
            if status[0] in ['A', 'M', 'D', 'R']:
                staged.append({"status": status[0], "file": filename})
            
            if status[1] in ['M', 'D']:
                unstaged.append({"status": status[1], "file": filename})
            
            if status == "??":
                untracked.append(filename)
        
        # Get current branch
        branch_result = await self._run_git_command(["branch", "--show-current"])
        current_branch = branch_result["stdout"].strip() if branch_result["success"] else "unknown"
        
        return {
            "success": True,
            "current_branch": current_branch,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0
        }
    
    async def commit_changes(
        self,
        message: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Create a commit with staged changes."""
        # Validate commit message
        if not message or len(message) < 10:
            return {
                "success": False,
                "error": "Commit message must be at least 10 characters"
            }
        
        # Check if there are staged changes
        status = await self.get_status()
        if not status["success"]:
            return status
        
        if not status["staged"]:
            return {
                "success": False,
                "error": "No changes staged for commit"
            }
        
        # Build commit command
        cmd_args = ["commit", "-m", message]
        
        # Add author info if provided
        if author_name and author_email:
            cmd_args.extend(["--author", f"{author_name} <{author_email}>"])
        
        # Execute commit
        result = await self._run_git_command(cmd_args)
        
        if result["success"]:
            # Get commit info
            info_result = await self._run_git_command(["log", "-1", "--oneline"])
            commit_info = info_result["stdout"].strip() if info_result["success"] else ""
            
            return {
                "success": True,
                "message": "Commit created successfully",
                "commit_info": commit_info,
                "files_committed": len(status["staged"])
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Commit failed")
            }
    
    async def stage_files(
        self,
        files: List[str],
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Stage files for commit."""
        if not files:
            return {
                "success": False,
                "error": "No files specified"
            }
        
        # Validate file paths
        valid_files = []
        for file in files:
            file_path = self.repo_path / file
            if file_path.exists() or file == ".":
                valid_files.append(file)
        
        if not valid_files:
            return {
                "success": False,
                "error": "No valid files found"
            }
        
        # Stage files
        result = await self._run_git_command(["add"] + valid_files)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Staged {len(valid_files)} files",
                "staged_files": valid_files
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to stage files")
            }
    
    async def unstage_files(
        self,
        files: List[str],
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Unstage files."""
        if not files:
            return {
                "success": False,
                "error": "No files specified"
            }
        
        # Unstage files
        result = await self._run_git_command(["reset", "HEAD", "--"] + files)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Unstaged {len(files)} files",
                "unstaged_files": files
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to unstage files")
            }
    
    async def get_log(
        self,
        limit: int = 10,
        oneline: bool = True,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get commit history."""
        cmd_args = ["log", f"-{limit}"]
        
        if oneline:
            cmd_args.append("--oneline")
        else:
            cmd_args.extend(["--pretty=format:%H|%an|%ae|%at|%s"])
        
        result = await self._run_git_command(cmd_args)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to get log")
            }
        
        if oneline:
            commits = result["stdout"].strip().split('\n') if result["stdout"] else []
        else:
            # Parse structured output
            commits = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "timestamp": int(parts[3]),
                            "message": parts[4]
                        })
        
        return {
            "success": True,
            "commits": commits,
            "count": len(commits)
        }
    
    async def get_diff(
        self,
        staged: bool = False,
        file_path: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Get differences (staged or unstaged)."""
        cmd_args = ["diff"]
        
        if staged:
            cmd_args.append("--cached")
        
        if file_path:
            cmd_args.append(file_path)
        
        result = await self._run_git_command(cmd_args)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to get diff")
            }
        
        diff_text = result["stdout"]
        
        # Parse diff to get summary
        files_changed = []
        additions = 0
        deletions = 0
        
        for line in diff_text.split('\n'):
            if line.startswith('+++') or line.startswith('---'):
                match = re.search(r'[ab]/(.+)$', line)
                if match and match.group(1) not in files_changed:
                    files_changed.append(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        return {
            "success": True,
            "diff": diff_text,
            "files_changed": files_changed,
            "additions": additions,
            "deletions": deletions,
            "has_changes": bool(diff_text.strip())
        }
    
    async def create_branch(
        self,
        branch_name: str,
        from_branch: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Create a new branch."""
        # Validate branch name
        if not re.match(r'^[a-zA-Z0-9/_-]+$', branch_name):
            return {
                "success": False,
                "error": "Invalid branch name. Use only letters, numbers, /, _, and -"
            }
        
        cmd_args = ["checkout", "-b", branch_name]
        
        if from_branch:
            cmd_args.append(from_branch)
        
        result = await self._run_git_command(cmd_args)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Created and switched to branch: {branch_name}",
                "branch": branch_name
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to create branch")
            }
    
    async def switch_branch(
        self,
        branch_name: str,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Switch to a different branch."""
        # Check for uncommitted changes
        status = await self.get_status()
        if not status["success"]:
            return status
        
        if not status["clean"]:
            return {
                "success": False,
                "error": "Cannot switch branches with uncommitted changes"
            }
        
        result = await self._run_git_command(["checkout", branch_name])
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Switched to branch: {branch_name}",
                "branch": branch_name
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to switch branch")
            }
    
    async def list_branches(
        self,
        include_remote: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """List all branches."""
        cmd_args = ["branch"]
        
        if include_remote:
            cmd_args.append("-a")
        
        result = await self._run_git_command(cmd_args)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to list branches")
            }
        
        branches = []
        current_branch = None
        
        for line in result["stdout"].strip().split('\n'):
            if line:
                if line.startswith('*'):
                    current_branch = line[2:].strip()
                    branches.append(current_branch)
                else:
                    branches.append(line.strip())
        
        return {
            "success": True,
            "branches": branches,
            "current_branch": current_branch,
            "count": len(branches)
        }
    
    async def pull_changes(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Pull changes from remote."""
        cmd_args = ["pull", remote]
        
        if branch:
            cmd_args.append(branch)
        
        result = await self._run_git_command(cmd_args)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Successfully pulled changes",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to pull changes")
            }
    
    async def push_changes(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        agent_type: str = None,
        task_id: int = None
    ) -> Dict[str, Any]:
        """Push changes to remote (with restrictions)."""
        if not self.allow_push:
            return {
                "success": False,
                "error": "Push operations are not allowed for this repository"
            }
        
        # Get current branch if not specified
        if not branch:
            status = await self.get_status()
            if not status["success"]:
                return status
            branch = status["current_branch"]
        
        # Check if branch is protected
        if branch in self.protected_branches and force:
            return {
                "success": False,
                "error": f"Cannot force push to protected branch: {branch}"
            }
        
        cmd_args = ["push", remote, branch]
        
        if force and branch not in self.protected_branches:
            cmd_args.append("--force")
        
        result = await self._run_git_command(cmd_args)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Successfully pushed to {remote}/{branch}",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("stderr", "Failed to push changes")
            }
    
    @property
    def name(self) -> str:
        """Return the server name."""
        return "github"
    
    @property
    def supported_operations(self) -> List[str]:
        """Return list of supported operations."""
        return [
            "get_status",
            "commit_changes",
            "stage_files",
            "unstage_files",
            "get_log",
            "get_diff",
            "create_branch",
            "switch_branch",
            "list_branches",
            "pull_changes",
            "push_changes"
        ]