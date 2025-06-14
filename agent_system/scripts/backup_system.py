#!/usr/bin/env python3
"""
System backup and restore utilities for the agent system.

This script provides comprehensive backup and restore capabilities for
the agent system, including database, configuration, and code state.

Usage:
    python scripts/backup_system.py backup                    # Create full backup
    python scripts/backup_system.py restore --backup-id ID   # Restore from backup
    python scripts/backup_system.py list                     # List available backups
    python scripts/backup_system.py cleanup --keep 5         # Keep only latest 5 backups
"""

import asyncio
import argparse
import sys
import os
import shutil
import json
import subprocess
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from core.database_manager import database


class SystemBackup:
    """Comprehensive system backup and restore functionality"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_system_root = self.project_root / "agent_system"
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self, description: str = None) -> str:
        """Create a comprehensive system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        print(f"📦 Creating system backup: {backup_id}")
        print("=" * 60)
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Create backup metadata
            metadata = await self._create_backup_metadata(backup_id, description)
            
            # 1. Backup database
            if not await self._backup_database(backup_path):
                return None
            
            # 2. Backup configuration
            if not await self._backup_configuration(backup_path):
                return None
            
            # 3. Backup code state
            if not await self._backup_code_state(backup_path):
                return None
            
            # 4. Backup documentation
            if not await self._backup_documentation(backup_path):
                return None
            
            # 5. Save metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # 6. Create compressed archive
            archive_path = await self._create_archive(backup_path, backup_id)
            
            # 7. Cleanup temporary files
            shutil.rmtree(backup_path)
            
            print(f"✅ Backup completed successfully: {archive_path}")
            print(f"Backup ID: {backup_id}")
            
            return backup_id
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            return None
    
    async def restore_backup(self, backup_id: str, confirm: bool = False) -> bool:
        """Restore system from backup"""
        archive_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        if not archive_path.exists():
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        if not confirm:
            print("⚠️  This will overwrite the current system state!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Restore cancelled.")
                return False
        
        print(f"🔄 Restoring system from backup: {backup_id}")
        print("=" * 60)
        
        try:
            # Extract backup
            temp_path = self.backup_dir / f"restore_{backup_id}"
            if temp_path.exists():
                shutil.rmtree(temp_path)
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(self.backup_dir)
            
            backup_path = self.backup_dir / backup_id
            
            # Load metadata
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    print(f"Restoring backup created: {metadata['timestamp']}")
                    if metadata.get('description'):
                        print(f"Description: {metadata['description']}")
            
            # 1. Restore database
            if not await self._restore_database(backup_path):
                return False
            
            # 2. Restore configuration
            if not await self._restore_configuration(backup_path):
                return False
            
            # 3. Restore code state (careful!)
            if not await self._restore_code_state(backup_path):
                return False
            
            # 4. Restore documentation
            if not await self._restore_documentation(backup_path):
                return False
            
            # Cleanup
            shutil.rmtree(backup_path)
            
            print("✅ System restore completed successfully!")
            print("⚠️  You may need to restart the system for changes to take effect.")
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            backup_id = backup_file.stem
            
            try:
                # Extract metadata without extracting full backup
                with tarfile.open(backup_file, 'r:gz') as tar:
                    metadata_member = None
                    for member in tar.getmembers():
                        if member.name.endswith('backup_metadata.json'):
                            metadata_member = member
                            break
                    
                    if metadata_member:
                        metadata_file = tar.extractfile(metadata_member)
                        metadata = json.load(metadata_file)
                        
                        backups.append({
                            "id": backup_id,
                            "timestamp": metadata.get('timestamp'),
                            "description": metadata.get('description', 'No description'),
                            "size_mb": round(backup_file.stat().st_size / 1024 / 1024, 1),
                            "git_commit": metadata.get('git_commit', 'Unknown'),
                            "git_branch": metadata.get('git_branch', 'Unknown')
                        })
                    else:
                        # Fallback for backups without metadata
                        stat = backup_file.stat()
                        backups.append({
                            "id": backup_id,
                            "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "description": "Legacy backup (no metadata)",
                            "size_mb": round(stat.st_size / 1024 / 1024, 1),
                            "git_commit": "Unknown",
                            "git_branch": "Unknown"
                        })
                        
            except Exception as e:
                print(f"⚠️  Could not read backup {backup_id}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    async def cleanup_backups(self, keep_count: int = 5) -> int:
        """Remove old backups, keeping only the latest N"""
        backups = await self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"Only {len(backups)} backups found, no cleanup needed.")
            return 0
        
        to_remove = backups[keep_count:]
        removed_count = 0
        
        for backup in to_remove:
            backup_file = self.backup_dir / f"{backup['id']}.tar.gz"
            if backup_file.exists():
                backup_file.unlink()
                print(f"🗑️  Removed backup: {backup['id']} ({backup['timestamp']})")
                removed_count += 1
        
        print(f"✅ Cleaned up {removed_count} old backups, kept {keep_count} latest.")
        return removed_count
    
    async def _create_backup_metadata(self, backup_id: str, description: str) -> Dict[str, Any]:
        """Create backup metadata"""
        metadata = {
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat(),
            "description": description or "Automatic system backup",
            "system_version": "1.0.0",  # TODO: Get from version file
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        # Add git information
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                metadata["git_commit"] = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                metadata["git_branch"] = result.stdout.strip()
                
        except Exception:
            pass
        
        # Add system statistics
        try:
            await database.initialize()
            
            agents = await database.agents.get_all_active()
            docs = await database.context_documents.get_all()
            tools = await database.tools.get_all_active()
            
            metadata["system_stats"] = {
                "agents_count": len(agents),
                "documents_count": len(docs),
                "tools_count": len(tools)
            }
        except Exception as e:
            metadata["system_stats"] = {"error": str(e)}
        
        return metadata
    
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
    
    async def _create_archive(self, backup_path: Path, backup_id: str) -> Path:
        """Create compressed archive of backup"""
        print("📦 Creating compressed archive...")
        
        archive_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_id)
        
        print(f"  ✅ Archive created: {archive_path}")
        return archive_path
    
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


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="System backup and restore utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create system backup')
    backup_parser.add_argument('--description', help='Backup description')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--backup-id', required=True, help='Backup ID to restore')
    restore_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Number of backups to keep')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return False
    
    backup_system = SystemBackup()
    
    try:
        if args.command == 'backup':
            backup_id = await backup_system.create_backup(args.description)
            return backup_id is not None
            
        elif args.command == 'restore':
            return await backup_system.restore_backup(args.backup_id, args.confirm)
            
        elif args.command == 'list':
            backups = await backup_system.list_backups()
            
            if not backups:
                print("No backups found.")
                return True
            
            print("📦 Available Backups:")
            print("=" * 80)
            print(f"{'ID':<25} {'Date':<20} {'Size':<8} {'Branch':<15} {'Description'}")
            print("-" * 80)
            
            for backup in backups:
                date_str = backup['timestamp'][:16].replace('T', ' ')
                print(f"{backup['id']:<25} {date_str:<20} {backup['size_mb']:<7}MB {backup['git_branch']:<15} {backup['description']}")
            
            return True
            
        elif args.command == 'cleanup':
            removed = await backup_system.cleanup_backups(args.keep)
            return True
            
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Operation failed: {e}")
        sys.exit(1)