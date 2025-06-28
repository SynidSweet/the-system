"""
Backup management functionality - listing and cleanup operations.
"""

import json
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .backup_utils import BackupUtils


class BackupManager:
    """Handles backup listing and cleanup operations"""
    
    def __init__(self, project_root: Path):
        self.utils = BackupUtils(project_root)
        self.backup_dir = self.utils.backup_dir
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
            backup_info = await self._extract_backup_info(backup_file)
            if backup_info:
                backups.append(backup_info)
        
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
    
    def display_backup_list(self, backups: List[Dict[str, Any]]):
        """Display formatted backup list"""
        if not backups:
            print("No backups found.")
            return
        
        self.utils.print_backup_status("list", "")
        print(f"{'ID':<25} {'Date':<20} {'Size':<8} {'Branch':<15} {'Description'}")
        print("-" * 80)
        
        for backup in backups:
            date_str = backup['timestamp'][:16].replace('T', ' ')
            size_str = self.utils.format_backup_size(backup['size_bytes'])
            print(f"{backup['id']:<25} {date_str:<20} {size_str:<8} {backup['git_branch']:<15} {backup['description']}")
    
    async def get_backup_info(self, backup_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific backup"""
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        if not backup_file.exists():
            return {"error": f"Backup {backup_id} not found"}
        
        backup_info = await self._extract_backup_info(backup_file)
        if backup_info:
            # Add validation information
            try:
                with tarfile.open(backup_file, 'r:gz') as tar:
                    members = [member.name for member in tar.getmembers()]
                    backup_info["contents"] = {
                        "database": any("agent_system.db" in member for member in members),
                        "config": any("config/" in member for member in members),
                        "code": any("code/" in member for member in members),
                        "docs": any("docs/" in member for member in members),
                        "total_files": len(members)
                    }
            except Exception as e:
                backup_info["contents"] = {"error": str(e)}
        
        return backup_info or {"error": f"Could not read backup {backup_id}"}
    
    async def _extract_backup_info(self, backup_file: Path) -> Dict[str, Any]:
        """Extract metadata from backup file"""
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
                    
                    return {
                        "id": backup_id,
                        "timestamp": metadata.get('timestamp'),
                        "description": metadata.get('description', 'No description'),
                        "size_mb": round(backup_file.stat().st_size / 1024 / 1024, 1),
                        "size_bytes": backup_file.stat().st_size,
                        "git_commit": metadata.get('git_commit', 'Unknown'),
                        "git_branch": metadata.get('git_branch', 'Unknown'),
                        "system_version": metadata.get('system_version', 'Unknown'),
                        "system_stats": metadata.get('system_stats', {})
                    }
                else:
                    # Fallback for backups without metadata
                    stat = backup_file.stat()
                    return {
                        "id": backup_id,
                        "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "description": "Legacy backup (no metadata)",
                        "size_mb": round(stat.st_size / 1024 / 1024, 1),
                        "size_bytes": stat.st_size,
                        "git_commit": "Unknown",
                        "git_branch": "Unknown",
                        "system_version": "Unknown",
                        "system_stats": {}
                    }
                    
        except Exception as e:
            print(f"⚠️  Could not read backup {backup_id}: {e}")
            return None
    
    def validate_backup_integrity(self, backup_id: str) -> Dict[str, Any]:
        """Validate backup file integrity"""
        backup_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        if not backup_file.exists():
            return {"valid": False, "error": "Backup file not found"}
        
        try:
            # Test archive integrity
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Attempt to list all members
                members = tar.getmembers()
                
                # Check for required files
                has_metadata = any(member.name.endswith('backup_metadata.json') for member in members)
                has_content = len(members) > 1  # More than just metadata
                
                return {
                    "valid": True,
                    "file_count": len(members),
                    "has_metadata": has_metadata,
                    "has_content": has_content,
                    "archive_readable": True
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": f"Archive corruption: {str(e)}",
                "archive_readable": False
            }