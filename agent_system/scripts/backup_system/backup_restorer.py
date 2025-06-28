"""
Backup restoration functionality for the agent system.
"""

import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from .backup_utils import BackupUtils


class BackupRestorer:
    """Handles restoration of system backups"""
    
    def __init__(self, project_root: Path):
        self.utils = BackupUtils(project_root)
        self.project_root = project_root
        self.agent_system_root = self.utils.agent_system_root
        self.backup_dir = self.utils.backup_dir
    
    async def restore_backup(self, backup_id: str, confirm: bool = False) -> bool:
        """Restore system from backup"""
        archive_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        if not archive_path.exists():
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        if not confirm and not self._confirm_restore():
            return False
        
        self.utils.print_backup_status("restore", backup_id)
        
        try:
            # Extract backup
            backup_path = await self._extract_backup(backup_id, archive_path)
            if not backup_path:
                return False
            
            # Validate backup structure
            validation = self.utils.validate_backup_structure(backup_path)
            if not validation["is_valid"]:
                print(f"❌ Invalid backup structure: {validation}")
                self._cleanup_restore(backup_path)
                return False
            
            # Load and display metadata
            metadata = self.utils.load_backup_metadata(backup_path)
            if metadata:
                print(f"Restoring backup created: {metadata['timestamp']}")
                if metadata.get('description'):
                    print(f"Description: {metadata['description']}")
            
            # Execute restore components in sequence
            restore_steps = [
                ("database", self._restore_database),
                ("configuration", self._restore_configuration),
                ("code", self._restore_code_state),
                ("documentation", self._restore_documentation)
            ]
            
            for step_name, step_func in restore_steps:
                if not await step_func(backup_path):
                    print(f"❌ Restore failed at step: {step_name}")
                    self._cleanup_restore(backup_path)
                    return False
            
            # Cleanup
            self._cleanup_restore(backup_path)
            
            print("✅ System restore completed successfully!")
            print("⚠️  You may need to restart the system for changes to take effect.")
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    async def _extract_backup(self, backup_id: str, archive_path: Path) -> Optional[Path]:
        """Extract backup archive"""
        try:
            # Remove any existing extraction
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(self.backup_dir)
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Failed to extract backup: {e}")
            return None
    
    async def _restore_database(self, backup_path: Path) -> bool:
        """Restore database from backup"""
        print("📊 Restoring database...")
        
        try:
            backup_db_path = backup_path / "agent_system.db"
            if backup_db_path.exists():
                current_db_path = self.agent_system_root / "agent_system.db"
                
                # Create backup of current database
                if current_db_path.exists():
                    current_backup = current_db_path.with_suffix('.db.backup')
                    shutil.copy2(current_db_path, current_backup)
                    print(f"  📦 Current database backed up to: {current_backup}")
                
                # Restore database
                shutil.copy2(backup_db_path, current_db_path)
                print(f"  ✅ Database restored")
            else:
                print("  ⚠️  No database in backup")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database restore failed: {e}")
            return False
    
    async def _restore_configuration(self, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        print("⚙️  Restoring configuration...")
        
        try:
            config_backup_path = backup_path / "config"
            
            if config_backup_path.exists():
                # Restore .env files
                for env_file in config_backup_path.glob("*.env*"):
                    if env_file.is_file():
                        target_path = self.agent_system_root / env_file.name
                        shutil.copy2(env_file, target_path)
                        print(f"  ✅ Config file restored: {env_file.name}")
                
                # Restore config directory
                config_dir_backup = config_backup_path / "config"
                if config_dir_backup.exists():
                    config_dir = self.agent_system_root / "config"
                    if config_dir.exists():
                        shutil.rmtree(config_dir)
                    shutil.copytree(config_dir_backup, config_dir)
                    print(f"  ✅ Config directory restored")
            else:
                print("  ⚠️  No configuration in backup")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Configuration restore failed: {e}")
            return False
    
    async def _restore_code_state(self, backup_path: Path) -> bool:
        """Restore code state from backup (be very careful!)"""
        print("💻 Restoring code state...")
        print("  ⚠️  This will overwrite current code!")
        
        try:
            code_backup_path = backup_path / "code"
            
            if not code_backup_path.exists():
                print("  ⚠️  No code state in backup")
                return True
            
            # Create backup of current code
            current_backup_dir = self.agent_system_root.parent / f"current_code_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(self.agent_system_root, current_backup_dir)
            print(f"  📦 Current code backed up to: {current_backup_dir}")
            
            # Restore directories
            for item in code_backup_path.iterdir():
                target_path = self.agent_system_root / item.name
                
                if item.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(item, target_path)
                else:
                    shutil.copy2(item, target_path)
                
                print(f"  ✅ Code restored: {item.name}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Code state restore failed: {e}")
            return False
    
    async def _restore_documentation(self, backup_path: Path) -> bool:
        """Restore documentation from backup"""
        print("📚 Restoring documentation...")
        
        try:
            docs_backup_path = backup_path / "docs"
            
            if docs_backup_path.exists():
                docs_dir = self.project_root / "docs"
                
                # Backup current docs
                if docs_dir.exists():
                    docs_backup = docs_dir.with_suffix('.backup')
                    if docs_backup.exists():
                        shutil.rmtree(docs_backup)
                    shutil.move(docs_dir, docs_backup)
                    print(f"  📦 Current docs backed up to: {docs_backup}")
                
                # Restore docs
                shutil.copytree(docs_backup_path, docs_dir)
                print(f"  ✅ Documentation restored")
            else:
                print("  ⚠️  No documentation in backup")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Documentation restore failed: {e}")
            return False
    
    def _confirm_restore(self) -> bool:
        """Confirm restore operation with user"""
        print("⚠️  This will overwrite the current system state!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Restore cancelled.")
            return False
        return True
    
    def _cleanup_restore(self, backup_path: Path):
        """Cleanup temporary restore files"""
        if backup_path.exists():
            shutil.rmtree(backup_path)