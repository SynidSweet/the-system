"""
Self-Modification Components

Modular components for safe self-modification workflows:
- ModificationValidator: Validation and testing
- BackupManager: Git state and rollback management  
- ChangeApplier: Documentation and change coordination
"""

from .backup_manager import BackupManager
from .change_applier import ChangeApplier
from .modification_validator import ModificationValidator

__all__ = [
    "BackupManager",
    "ChangeApplier", 
    "ModificationValidator"
]