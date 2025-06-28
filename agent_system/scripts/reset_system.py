#!/usr/bin/env python3
"""
System reset utility for the agent system.

This script resets the system to a fresh, uninitialized state by:
1. Optionally creating a backup
2. Removing the database
3. Clearing knowledge entities
4. Removing logs
5. Resetting configuration

Usage:
    python scripts/reset_system.py           # Reset without backup
    python scripts/reset_system.py --backup  # Create backup before reset
    python scripts/reset_system.py --force   # Skip confirmation
"""

import asyncio
import argparse
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    parser = argparse.ArgumentParser(description='Reset the agent system to fresh state')
    parser.add_argument('--backup', action='store_true', help='Create backup before reset')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    knowledge_dir = project_root / "knowledge"
    logs_dir = project_root / "logs"
    
    print("🔄 System Reset Utility")
    print("=" * 60)
    print("This will reset the system to a fresh, uninitialized state.")
    print("The following will be removed:")
    print("  - Database (agent_system.db)")
    print("  - Knowledge entities")
    print("  - Logs")
    print("  - Runtime state")
    print("=" * 60)
    
    # Confirmation
    if not args.force:
        response = input("Are you sure you want to reset the system? (yes/no): ")
        if response.lower() != 'yes':
            print("Reset cancelled.")
            return
    
    # Create backup if requested
    if args.backup:
        print("\n📦 Creating backup before reset...")
        try:
            from scripts.backup_system import SystemBackup
            backup = SystemBackup()
            backup_id = await backup.create_backup(description="Pre-reset backup")
            if backup_id:
                print(f"✅ Backup created: {backup_id}")
            else:
                print("❌ Backup failed. Continue anyway? (yes/no): ")
                if input().lower() != 'yes':
                    return
        except Exception as e:
            print(f"❌ Backup error: {e}")
            print("Continue anyway? (yes/no): ")
            if input().lower() != 'yes':
                return
    
    # Stop services if running
    print("\n🛑 Stopping services...")
    svc_script = project_root / "svc"
    if svc_script.exists():
        os.system(f"{svc_script} stop")
    
    # Remove database
    print("\n🗑️  Removing database...")
    db_file = data_dir / "agent_system.db"
    if db_file.exists():
        db_file.unlink()
        print("  ✅ Database removed")
    else:
        print("  ℹ️  No database found")
    
    # Remove knowledge entities
    print("\n🗑️  Removing knowledge entities...")
    if knowledge_dir.exists():
        # Keep the directory structure but remove all JSON files
        removed_count = 0
        for json_file in knowledge_dir.rglob("*.json"):
            json_file.unlink()
            removed_count += 1
        print(f"  ✅ Removed {removed_count} knowledge entities")
    else:
        print("  ℹ️  No knowledge directory found")
    
    # Clear logs
    print("\n🗑️  Clearing logs...")
    if logs_dir.exists():
        log_count = 0
        for log_file in logs_dir.glob("*.log"):
            log_file.unlink()
            log_count += 1
        for pid_file in logs_dir.glob("*.pid"):
            pid_file.unlink()
        print(f"  ✅ Removed {log_count} log files")
    else:
        print("  ℹ️  No logs directory found")
    
    # Remove any cached data
    print("\n🗑️  Clearing cached data...")
    cache_dirs = [
        project_root / "__pycache__",
        project_root / ".pytest_cache",
        project_root / "web" / "node_modules" / ".cache"
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✅ Removed {cache_dir.name}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {cache_dir.name}: {e}")
    
    # Create necessary directories
    print("\n📁 Creating fresh directories...")
    data_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    knowledge_dir.mkdir(exist_ok=True)
    
    # Create knowledge subdirectories
    for subdir in ["domains", "processes", "agents", "tools", "patterns", "system"]:
        (knowledge_dir / subdir).mkdir(exist_ok=True)
    
    print("\n✅ System reset complete!")
    print("\nNext steps:")
    print("1. Start the system: ./svc start")
    print("2. Open http://localhost:3000 to initialize")
    print("   OR")
    print("   Run: python scripts/seed_system.py")
    print("\nThe system is now in an uninitialized state.")


if __name__ == "__main__":
    asyncio.run(main())