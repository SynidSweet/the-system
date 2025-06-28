#!/usr/bin/env python3
"""
Backup Manager Component

Handles git state management, branch creation, and emergency rollback procedures
for safe self-modification workflows.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class BackupManager:
    """Manages git state, branches, and rollback procedures for self-modification"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.original_branch: Optional[str] = None
        self.development_branch: Optional[str] = None
        
    async def save_current_state(self, task_description: str, agent_name: str) -> bool:
        """Save current working state before making changes"""
        print("📦 Saving current state...")
        
        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                print("  📝 Working directory has changes, committing...")
                
                # Add all changes
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.project_root,
                    check=True
                )
                
                # Create snapshot commit
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                commit_message = f"""Snapshot before self-improvement: {task_description[:50]}

🤖 Self-improvement initiated by {agent_name}
📋 Task: {task_description}
🎯 Goal: System enhancement and optimization

Co-Authored-By: Claude <noreply@anthropic.com>"""
                
                subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    cwd=self.project_root,
                    check=True
                )
                
                print("  ✅ Snapshot commit created")
            else:
                print("  ✅ Working directory clean, no snapshot needed")
                
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            self.original_branch = result.stdout.strip()
            print(f"  📍 Current branch: {self.original_branch}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Git operation failed: {e}")
            return False
    
    async def create_development_branch(self, task_description: str) -> bool:
        """Create a new development branch for the changes"""
        print("🌿 Creating development branch...")
        
        try:
            # Create branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_slug = "".join(c if c.isalnum() else "-" for c in task_description[:30]).strip("-")
            self.development_branch = f"self-improvement-{task_slug}-{timestamp}"
            
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", self.development_branch],
                cwd=self.project_root,
                check=True
            )
            
            print(f"  ✅ Created and switched to branch: {self.development_branch}")
            
            # Push branch to establish remote tracking
            try:
                subprocess.run(
                    ["git", "push", "-u", "origin", self.development_branch],
                    cwd=self.project_root,
                    check=True
                )
                print("  ✅ Development branch pushed to remote")
            except subprocess.CalledProcessError:
                print("  ⚠️  Remote push failed (remote may not be configured)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Branch creation failed: {e}")
            return False
    
    async def create_final_commit(self, task_description: str, agent_name: str) -> bool:
        """Create final commit with all changes"""
        print("💾 Creating final commit...")
        
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True
            )
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print("  ✅ No changes to commit")
                return True
            
            # Create final commit
            commit_message = f"""Implement self-improvement: {task_description}

🤖 Self-modification completed by {agent_name}
📋 Task: {task_description}
🔧 Changes implemented and tested
✅ Health checks passed

This commit represents a successful self-improvement cycle following
the procedures outlined in docs/self_improvement_guide.md.

🤖 Generated with Claude Code Self-Modification Workflow

Co-Authored-By: Claude <noreply@anthropic.com>"""

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                check=True
            )
            
            print("  ✅ Final commit created")
            
            # Push changes
            try:
                subprocess.run(
                    ["git", "push", "origin", self.development_branch],
                    cwd=self.project_root,
                    check=True
                )
                print("  ✅ Changes pushed to remote")
            except subprocess.CalledProcessError:
                print("  ⚠️  Remote push failed")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Commit creation failed: {e}")
            return False
    
    async def emergency_rollback(self, task_description: str, agent_name: str, send_notification_func=None) -> bool:
        """Emergency rollback procedure"""
        print("\n🚨 Executing emergency rollback...")
        
        try:
            # Switch back to original branch
            if self.original_branch:
                subprocess.run(
                    ["git", "checkout", self.original_branch],
                    cwd=self.project_root,
                    check=True
                )
                print(f"  ✅ Switched back to {self.original_branch}")
            
            # Send emergency notification if callback provided
            if send_notification_func:
                await send_notification_func(
                    f"🚨 EMERGENCY ROLLBACK EXECUTED\n"
                    f"Task: {task_description}\n"
                    f"Agent: {agent_name}\n"
                    f"Returned to branch: {self.original_branch}\n"
                    f"Development branch preserved: {self.development_branch}",
                    "error",
                    priority="urgent"
                )
            
            return True
            
        except Exception as e:
            print(f"  ❌ Emergency rollback failed: {e}")
            return False
    
    async def get_git_status(self) -> Tuple[bool, str]:
        """Get current git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, f"Git status failed: {e}"
    
    async def create_backup_tag(self, task_description: str) -> bool:
        """Create a backup tag for easy restoration"""
        print("🏷️ Creating backup tag...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            tag_name = f"backup-{timestamp}"
            
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Backup before: {task_description}"],
                cwd=self.project_root,
                check=True
            )
            
            print(f"  ✅ Backup tag created: {tag_name}")
            
            # Try to push tag to remote
            try:
                subprocess.run(
                    ["git", "push", "origin", tag_name],
                    cwd=self.project_root,
                    check=True
                )
                print("  ✅ Backup tag pushed to remote")
            except subprocess.CalledProcessError:
                print("  ⚠️  Tag push failed (remote may not be configured)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Backup tag creation failed: {e}")
            return False
    
    async def validate_git_repository(self) -> bool:
        """Validate that we're in a git repository and it's functional"""
        print("🔍 Validating git repository...")
        
        try:
            # Check if this is a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            git_dir = result.stdout.strip()
            print(f"  ✅ Git repository found: {git_dir}")
            
            # Check if we have any commits
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Repository has commit history")
                return True
            else:
                print("  ⚠️  Repository has no commits yet")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Git validation failed: {e}")
            return False
    
    def get_original_branch(self) -> Optional[str]:
        """Get the original branch name"""
        return self.original_branch
    
    def get_development_branch(self) -> Optional[str]:
        """Get the development branch name"""
        return self.development_branch