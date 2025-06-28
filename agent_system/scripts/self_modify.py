#!/usr/bin/env python3
"""
Self-modification workflow helper for the agent system.

This script implements the complete self-improvement workflow described in 
docs/self_improvement_guide.md with proper branch management and safety procedures.

Now uses modular components for better maintainability:
- BackupManager: Git state and rollback management
- ChangeApplier: Documentation and change coordination  
- ModificationValidator: Validation and testing

Usage:
    python scripts/self_modify.py --task-description "Description of improvement"
    python scripts/self_modify.py --agent-name agent_name --task-id task_id
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database_manager import database
from tools.system_tools.user_communication import SendMessageToUserTool
from .self_modify import BackupManager, ChangeApplier, ModificationValidator


class SelfModificationWorkflow:
    """Implements the complete self-modification workflow with safety checks using modular components"""
    
    def __init__(self, task_description: str, agent_name: Optional[str] = None, task_id: Optional[str] = None):
        self.task_description = task_description
        self.agent_name = agent_name or "system"
        self.task_id = task_id
        self.project_root = Path(__file__).parent.parent.parent
        self.user_messenger = SendMessageToUserTool()
        
        # Initialize modular components
        self.backup_manager = BackupManager(self.project_root)
        self.change_applier = ChangeApplier(self.project_root)
        self.validator = ModificationValidator(self.project_root)
        
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
            await self.change_applier.run_implementation_phase(
                self.task_description,
                self.agent_name,
                self.backup_manager.get_development_branch(),
                self._send_user_message
            )
            
            # Phase 3: Testing and Validation (post-implementation)
            if not await self.validator.run_full_validation_suite():
                return False
                
            # Phase 4: Documentation and Maintenance
            if not await self.change_applier.coordinate_documentation_phase(
                self.task_description,
                self.agent_name,
                self.backup_manager.get_development_branch()
            ):
                return False
                
            # Create final commit
            if not await self.backup_manager.create_final_commit(self.task_description, self.agent_name):
                return False
                
            print("\n✅ Self-modification workflow completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Self-modification workflow failed: {e}")
            await self.backup_manager.emergency_rollback(
                self.task_description,
                self.agent_name,
                self._send_user_message
            )
            return False
    
    async def _phase_1_preparation(self) -> bool:
        """Phase 1: Preparation and Planning using modular components"""
        print("\n📋 Phase 1: Preparation and Planning")
        
        # Step 1: Save current state
        if not await self.backup_manager.save_current_state(self.task_description, self.agent_name):
            return False
            
        # Step 2: Create development branch
        if not await self.backup_manager.create_development_branch(self.task_description):
            return False
            
        # Step 3: Document improvement plan
        plan_file = await self.change_applier.document_improvement_plan(
            self.task_description,
            self.agent_name,
            self.task_id,
            self.backup_manager.get_development_branch(),
            self.backup_manager.get_original_branch()
        )
        if not plan_file:
            return False
            
        # Step 4: Set up testing plan
        test_file = await self.validator.create_testing_plan(
            self.task_description,
            self.backup_manager.get_development_branch()
        )
        if not test_file:
            return False
            
        print("✅ Phase 1 completed - Environment ready for implementation")
        return True
    
    async def _send_user_message(self, message: str, message_type: str = "info", priority: str = "normal"):
        """Send message to user through the system"""
        await self.change_applier.send_user_notification(
            message=message,
            message_type=message_type,
            priority=priority,
            task_id=self.task_id,
            user_messenger=self.user_messenger
        )


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