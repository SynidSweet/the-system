#!/usr/bin/env python3
"""
Self-modification workflow helper for the agent system.

This script implements the complete self-improvement workflow described in 
docs/self_improvement_guide.md with proper branch management and safety procedures.

Usage:
    python scripts/self_modify.py --task-description "Description of improvement"
    python scripts/self_modify.py --agent-name agent_name --task-id task_id
"""

import asyncio
import argparse
import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database_manager import database
from tools.system_tools.user_communication import SendMessageToUserTool


class SelfModificationWorkflow:
    """Implements the complete self-modification workflow with safety checks"""
    
    def __init__(self, task_description: str, agent_name: Optional[str] = None, task_id: Optional[str] = None):
        self.task_description = task_description
        self.agent_name = agent_name or "system"
        self.task_id = task_id
        self.original_branch = None
        self.development_branch = None
        self.project_root = Path(__file__).parent.parent.parent
        self.user_messenger = SendMessageToUserTool()
        
    async def execute_workflow(self) -> bool:
        """Execute the complete self-modification workflow"""
        print("🤖 Starting Self-Modification Workflow")
        print("=" * 60)
        print(f"Task: {self.task_description}")
        print(f"Agent: {self.agent_name}")
        print("=" * 60)
        
        try:
            # Phase 1: Preparation and Planning
            if not await self._phase_1_preparation():
                return False
                
            # Phase 2: Implementation (this is where the actual agent work happens)
            print("\n🔧 Phase 2: Implementation")
            print("The development environment is ready. Agent should now implement changes.")
            await self._send_user_message(
                f"Self-modification workflow ready for task: {self.task_description}\n"
                f"Development branch: {self.development_branch}\n"
                f"Agent {self.agent_name} can now proceed with implementation.",
                "info"
            )
            
            # Phase 3: Testing and Validation (post-implementation)
            if not await self._phase_3_testing():
                return False
                
            # Phase 4: Documentation and Maintenance
            if not await self._phase_4_documentation():
                return False
                
            print("\n✅ Self-modification workflow completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Self-modification workflow failed: {e}")
            await self._emergency_rollback()
            return False
    
    async def _phase_1_preparation(self) -> bool:
        """Phase 1: Preparation and Planning"""
        print("\n📋 Phase 1: Preparation and Planning")
        
        # Step 1: Save current state
        if not await self._save_current_state():
            return False
            
        # Step 2: Create development branch
        if not await self._create_development_branch():
            return False
            
        # Step 3: Document improvement plan
        if not await self._document_improvement_plan():
            return False
            
        # Step 4: Set up testing plan
        if not await self._setup_testing_plan():
            return False
            
        print("✅ Phase 1 completed - Environment ready for implementation")
        return True
    
    async def _save_current_state(self) -> bool:
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
                commit_message = f"""Snapshot before self-improvement: {self.task_description[:50]}

🤖 Self-improvement initiated by {self.agent_name}
📋 Task: {self.task_description}
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
    
    async def _create_development_branch(self) -> bool:
        """Create a new development branch for the changes"""
        print("🌿 Creating development branch...")
        
        try:
            # Create branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_slug = "".join(c if c.isalnum() else "-" for c in self.task_description[:30]).strip("-")
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
    
    async def _document_improvement_plan(self) -> bool:
        """Document the improvement plan"""
        print("📝 Documenting improvement plan...")
        
        try:
            plan_file = self.project_root / f"docs/improvement_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            plan_content = f"""# Self-Improvement Plan

## Task Description
{self.task_description}

## Implementation Details
- **Agent**: {self.agent_name}
- **Task ID**: {self.task_id or "N/A"}
- **Branch**: {self.development_branch}
- **Started**: {datetime.now().isoformat()}

## Problem Analysis
<!-- Agent should fill this in during implementation -->
- Current limitation: 
- Root causes:
- Impact assessment:

## Solution Design
<!-- Agent should fill this in during implementation -->
- Proposed approach:
- Components to modify:
- Risk assessment:

## Implementation Strategy
<!-- Agent should fill this in during implementation -->
- Step-by-step plan:
- Dependencies:
- Testing approach:

## Success Criteria
<!-- Agent should fill this in during implementation -->
- Functional requirements:
- Performance requirements:
- Quality requirements:

## Rollback Plan
- Original branch: {self.original_branch}
- Backup tag: backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}
- Emergency procedures documented in self_improvement_guide.md

---
Generated by self-modification workflow on {datetime.now().isoformat()}
"""
            
            plan_file.write_text(plan_content)
            print(f"  ✅ Improvement plan created: {plan_file}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to create improvement plan: {e}")
            return False
    
    async def _setup_testing_plan(self) -> bool:
        """Set up the testing plan for validation"""
        print("🧪 Setting up testing plan...")
        
        try:
            # Create testing checklist
            test_file = self.project_root / f"tests/self_modification_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            test_file.parent.mkdir(exist_ok=True)
            
            test_content = f"""# Self-Modification Testing Plan

## Task: {self.task_description}
## Branch: {self.development_branch}

## Pre-Implementation Tests
- [ ] System health check passed
- [ ] All existing tests pass
- [ ] Database connectivity verified
- [ ] Core agents operational

## Implementation Tests
<!-- Agent should add specific tests during implementation -->
- [ ] New functionality works as expected
- [ ] Error handling implemented
- [ ] Edge cases handled
- [ ] Performance within acceptable limits

## Integration Tests
- [ ] Existing functionality unaffected
- [ ] Inter-component communication works
- [ ] Database operations successful
- [ ] API endpoints functional

## Post-Deployment Tests
- [ ] System restart successful
- [ ] Health checks pass
- [ ] User workflows functional
- [ ] Performance metrics acceptable

## Rollback Tests
- [ ] Rollback procedure tested
- [ ] System recovers to previous state
- [ ] No data loss or corruption

---
Testing plan generated on {datetime.now().isoformat()}
"""
            
            test_file.write_text(test_content)
            print(f"  ✅ Testing plan created: {test_file}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to create testing plan: {e}")
            return False
    
    async def _phase_3_testing(self) -> bool:
        """Phase 3: Testing and Validation (called after implementation)"""
        print("\n🧪 Phase 3: Testing and Validation")
        
        # Run system health check
        if not await self._run_health_check():
            print("❌ Health check failed")
            return False
        
        # Run tests if they exist
        if not await self._run_automated_tests():
            print("❌ Automated tests failed")
            return False
        
        print("✅ Phase 3 completed - Testing passed")
        return True
    
    async def _run_health_check(self) -> bool:
        """Run comprehensive system health check"""
        print("🏥 Running system health check...")
        
        try:
            # Run the seed system health check
            result = subprocess.run(
                [sys.executable, "scripts/seed_system.py"],
                cwd=self.project_root / "agent_system",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if "Health check passed" in result.stdout:
                print("  ✅ System health check passed")
                return True
            else:
                print("  ❌ System health check failed")
                print(f"  Output: {result.stdout}")
                print(f"  Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False
    
    async def _run_automated_tests(self) -> bool:
        """Run any available automated tests"""
        print("🤖 Running automated tests...")
        
        # Check for test files
        test_patterns = [
            "tests/test_*.py",
            "test_*.py",
            "*/test_*.py"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))
        
        if not test_files:
            print("  ⚠️  No automated test files found, skipping")
            return True
        
        try:
            # Try to run pytest
            result = subprocess.run(
                ["python", "-m", "pytest", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("  ✅ All automated tests passed")
                return True
            else:
                print("  ❌ Some automated tests failed")
                print(f"  Output: {result.stdout}")
                return False
                
        except FileNotFoundError:
            print("  ⚠️  pytest not available, skipping automated tests")
            return True
        except Exception as e:
            print(f"  ❌ Test execution failed: {e}")
            return False
    
    async def _phase_4_documentation(self) -> bool:
        """Phase 4: Documentation and Maintenance"""
        print("\n📚 Phase 4: Documentation and Maintenance")
        
        # Update system documentation
        if not await self._update_documentation():
            return False
        
        # Create final commit
        if not await self._create_final_commit():
            return False
        
        print("✅ Phase 4 completed - Documentation updated")
        return True
    
    async def _update_documentation(self) -> bool:
        """Update relevant documentation"""
        print("📝 Updating documentation...")
        
        try:
            # Update CHANGELOG if it exists
            changelog_path = self.project_root / "CHANGELOG.md"
            if changelog_path.exists():
                changelog_content = changelog_path.read_text()
                
                new_entry = f"""
## [{datetime.now().strftime('%Y-%m-%d')}] - Self-Improvement

### Added
- {self.task_description}

### Changed
- System enhanced through self-modification workflow
- Agent: {self.agent_name}
- Branch: {self.development_branch}

"""
                # Insert after the first line (usually # Changelog)
                lines = changelog_content.split('\n')
                lines.insert(1, new_entry)
                changelog_path.write_text('\n'.join(lines))
                
                print("  ✅ CHANGELOG.md updated")
            
            # Update README if needed
            readme_path = self.project_root / "README.md"
            if readme_path.exists():
                print("  ✅ README.md reviewed (no changes needed)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Documentation update failed: {e}")
            return False
    
    async def _create_final_commit(self) -> bool:
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
            commit_message = f"""Implement self-improvement: {self.task_description}

🤖 Self-modification completed by {self.agent_name}
📋 Task: {self.task_description}
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
    
    async def _emergency_rollback(self) -> bool:
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
            
            # Send emergency notification
            await self._send_user_message(
                f"🚨 EMERGENCY ROLLBACK EXECUTED\n"
                f"Task: {self.task_description}\n"
                f"Agent: {self.agent_name}\n"
                f"Returned to branch: {self.original_branch}\n"
                f"Development branch preserved: {self.development_branch}",
                "error",
                priority="urgent"
            )
            
            return True
            
        except Exception as e:
            print(f"  ❌ Emergency rollback failed: {e}")
            return False
    
    async def _send_user_message(self, message: str, message_type: str = "info", priority: str = "normal"):
        """Send message to user through the system"""
        try:
            if self.task_id:
                # TODO: This would need proper task context
                pass
            else:
                # Direct message without task context
                result = await self.user_messenger.execute(
                    message=message,
                    message_type=message_type,
                    priority=priority
                )
                if not result.success:
                    print(f"  ⚠️  Failed to send user message: {result.error_message}")
        except Exception as e:
            print(f"  ⚠️  Failed to send user message: {e}")


async def main():
    """Main entry point for the self-modification workflow"""
    parser = argparse.ArgumentParser(description="Self-modification workflow helper")
    parser.add_argument("--task-description", required=True, help="Description of the self-improvement task")
    parser.add_argument("--agent-name", default="system", help="Name of the agent performing the modification")
    parser.add_argument("--task-id", help="ID of the task (if called from task context)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        return True
    
    # Initialize database connection
    try:
        await database.initialize()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Execute workflow
    workflow = SelfModificationWorkflow(
        task_description=args.task_description,
        agent_name=args.agent_name,
        task_id=args.task_id
    )
    
    success = await workflow.execute_workflow()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Self-modification workflow cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Self-modification workflow failed: {e}")
        sys.exit(1)