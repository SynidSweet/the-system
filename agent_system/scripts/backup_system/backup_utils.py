"""
Shared utilities and metadata handling for backup operations.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.database import db_manager
database = db_manager


class BackupUtils:
    """Shared utilities for backup operations"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.agent_system_root = project_root / "agent_system"
        self.backup_dir = project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def generate_backup_id(self) -> str:
        """Generate a unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
    
    async def create_backup_metadata(self, backup_id: str, description: str) -> Dict[str, Any]:
        """Create comprehensive backup metadata"""
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
    
    def load_backup_metadata(self, backup_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata from backup directory"""
        metadata_file = backup_path / "backup_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_backup_metadata(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Save metadata to backup directory"""
        try:
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Failed to save metadata: {e}")
            return False
    
    def get_backup_paths(self, backup_id: str = None) -> Dict[str, Path]:
        """Get standardized backup paths"""
        if backup_id:
            return {
                "backup_dir": self.backup_dir / backup_id,
                "archive_path": self.backup_dir / f"{backup_id}.tar.gz",
                "temp_dir": self.backup_dir / f"temp_{backup_id}"
            }
        else:
            return {
                "backup_root": self.backup_dir,
                "project_root": self.project_root,
                "agent_system_root": self.agent_system_root
            }
    
    def validate_backup_structure(self, backup_path: Path) -> Dict[str, bool]:
        """Validate backup directory structure"""
        validation = {
            "metadata": (backup_path / "backup_metadata.json").exists(),
            "database": (backup_path / "agent_system.db").exists(),
            "config": (backup_path / "config").exists(),
            "code": (backup_path / "code").exists(),
            "docs": (backup_path / "docs").exists()
        }
        
        validation["is_valid"] = all([
            validation["metadata"],
            any([validation["database"], validation["config"], validation["code"]])
        ])
        
        return validation
    
    def print_backup_status(self, operation: str, backup_id: str):
        """Print standardized backup operation headers"""
        if operation == "create":
            print(f"📦 Creating system backup: {backup_id}")
        elif operation == "restore":
            print(f"🔄 Restoring system from backup: {backup_id}")
        elif operation == "list":
            print("📦 Available Backups:")
        elif operation == "cleanup":
            print("🧹 Cleaning up old backups...")
        
        print("=" * 60)
    
    def format_backup_size(self, size_bytes: int) -> str:
        """Format backup size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{round(size_bytes / 1024, 1)}KB"
        else:
            return f"{round(size_bytes / 1024 / 1024, 1)}MB"