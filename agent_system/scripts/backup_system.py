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
from pathlib import Path
from typing import Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backup_system import BackupCreator, BackupRestorer, BackupManager


class SystemBackup:
    """Main orchestrator for backup operations using modular components"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.creator = BackupCreator(self.project_root)
        self.restorer = BackupRestorer(self.project_root)
        self.manager = BackupManager(self.project_root)
    
    async def create_backup(self, description: str = None) -> Optional[str]:
        """Create a comprehensive system backup"""
        return await self.creator.create_backup(description)
    
    async def restore_backup(self, backup_id: str, confirm: bool = False) -> bool:
        """Restore system from backup"""
        return await self.restorer.restore_backup(backup_id, confirm)
    
    async def list_backups(self):
        """List all available backups"""
        backups = await self.manager.list_backups()
        self.manager.display_backup_list(backups)
        return len(backups) > 0
    
    async def cleanup_backups(self, keep_count: int = 5) -> bool:
        """Remove old backups, keeping only the latest N"""
        removed_count = await self.manager.cleanup_backups(keep_count)
        return True


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