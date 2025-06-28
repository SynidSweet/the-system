"""
Backup creation functionality for the agent system.
"""

import shutil
import tarfile
from pathlib import Path
from typing import Optional

from .backup_utils import BackupUtils


class BackupCreator:
    """Handles creation of system backups"""
    
    def __init__(self, project_root: Path):
        self.utils = BackupUtils(project_root)
        self.project_root = project_root
        self.agent_system_root = self.utils.agent_system_root
        self.backup_dir = self.utils.backup_dir
    
    async def create_backup(self, description: str = None) -> Optional[str]:
        """Create a comprehensive system backup"""
        backup_id = self.utils.generate_backup_id()
        backup_path = self.backup_dir / backup_id
        
        self.utils.print_backup_status("create", backup_id)
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Create backup metadata
            metadata = await self.utils.create_backup_metadata(backup_id, description)
            
            # Execute backup components in sequence
            backup_steps = [
                ("database", self._backup_database),
                ("configuration", self._backup_configuration),
                ("code", self._backup_code_state),
                ("documentation", self._backup_documentation)
            ]
            
            for step_name, step_func in backup_steps:
                if not await step_func(backup_path):
                    print(f"❌ Backup failed at step: {step_name}")
                    self._cleanup_failed_backup(backup_path)
                    return None
            
            # Save metadata
            if not self.utils.save_backup_metadata(backup_path, metadata):
                self._cleanup_failed_backup(backup_path)
                return None
            
            # Create compressed archive
            archive_path = await self._create_archive(backup_path, backup_id)
            if not archive_path:
                self._cleanup_failed_backup(backup_path)
                return None
            
            # Cleanup temporary files
            shutil.rmtree(backup_path)
            
            print(f"✅ Backup completed successfully: {archive_path}")
            print(f"Backup ID: {backup_id}")
            
            return backup_id
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            self._cleanup_failed_backup(backup_path)
            return None
    
    async def _backup_database(self, backup_path: Path) -> bool:
        """Backup the SQLite database"""
        print("📊 Backing up database...")
        
        try:
            db_path = self.agent_system_root / "agent_system.db"
            if db_path.exists():
                backup_db_path = backup_path / "agent_system.db"
                shutil.copy2(db_path, backup_db_path)
                print(f"  ✅ Database backed up: {backup_db_path}")
            else:
                print("  ⚠️  Database file not found, skipping")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database backup failed: {e}")
            return False
    
    async def _backup_configuration(self, backup_path: Path) -> bool:
        """Backup configuration files"""
        print("⚙️  Backing up configuration...")
        
        try:
            config_backup_path = backup_path / "config"
            config_backup_path.mkdir(exist_ok=True)
            
            # Backup .env files
            for env_file in self.agent_system_root.glob("*.env*"):
                if env_file.is_file():
                    shutil.copy2(env_file, config_backup_path)
                    print(f"  ✅ Config file backed up: {env_file.name}")
            
            # Backup config directory
            config_dir = self.agent_system_root / "config"
            if config_dir.exists():
                shutil.copytree(config_dir, config_backup_path / "config", dirs_exist_ok=True)
                print(f"  ✅ Config directory backed up")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Configuration backup failed: {e}")
            return False
    
    async def _backup_code_state(self, backup_path: Path) -> bool:
        """Backup current code state"""
        print("💻 Backing up code state...")
        
        try:
            code_backup_path = backup_path / "code"
            code_backup_path.mkdir(exist_ok=True)
            
            # Important directories to backup
            important_dirs = [
                "core",
                "tools", 
                "api",
                "scripts",
                "web/src"  # Just the source, not node_modules
            ]
            
            for dir_name in important_dirs:
                source_dir = self.agent_system_root / dir_name
                if source_dir.exists():
                    if source_dir.is_dir():
                        shutil.copytree(source_dir, code_backup_path / dir_name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_dir, code_backup_path / dir_name)
                    print(f"  ✅ Code backed up: {dir_name}")
            
            # Backup important files
            important_files = [
                "requirements.txt",
                "package.json",
                "README.md"
            ]
            
            for file_name in important_files:
                source_file = self.agent_system_root / file_name
                if source_file.exists():
                    shutil.copy2(source_file, code_backup_path)
                    print(f"  ✅ File backed up: {file_name}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Code state backup failed: {e}")
            return False
    
    async def _backup_documentation(self, backup_path: Path) -> bool:
        """Backup documentation"""
        print("📚 Backing up documentation...")
        
        try:
            docs_dir = self.project_root / "docs"
            if docs_dir.exists():
                backup_docs_path = backup_path / "docs"
                shutil.copytree(docs_dir, backup_docs_path, dirs_exist_ok=True)
                print(f"  ✅ Documentation backed up")
            else:
                print("  ⚠️  Documentation directory not found")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Documentation backup failed: {e}")
            return False
    
    async def _create_archive(self, backup_path: Path, backup_id: str) -> Optional[Path]:
        """Create compressed archive of backup"""
        print("📦 Creating compressed archive...")
        
        try:
            archive_path = self.backup_dir / f"{backup_id}.tar.gz"
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_id)
            
            print(f"  ✅ Archive created: {archive_path}")
            return archive_path
            
        except Exception as e:
            print(f"  ❌ Archive creation failed: {e}")
            return None
    
    def _cleanup_failed_backup(self, backup_path: Path):
        """Cleanup after failed backup"""
        if backup_path.exists():
            shutil.rmtree(backup_path)
            print(f"🧹 Cleaned up failed backup: {backup_path}")