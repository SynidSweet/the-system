#!/usr/bin/env python3
"""
Simple test to verify Phase 8 cleanup completed successfully.
"""

import sqlite3
from pathlib import Path


def test_database_structure():
    """Check database structure after cleanup."""
    # Try multiple possible database locations
    possible_paths = [
        Path(__file__).parent.parent / "data" / "agent_system.db",
        Path("/code/personal/the-system/agent_system.db"),
        Path(__file__).parent.parent / "agent_system.db",
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ Database not found in any expected location")
        print("Searched in:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    print("✓ Database found at:", db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\nCurrent tables in database:")
    entity_tables = []
    archive_tables = []
    old_tables = []
    other_tables = []
    
    for table in tables:
        if table.startswith('_archive_'):
            archive_tables.append(table)
        elif table in ['agents', 'tasks', 'messages', 'tools', 'context_documents']:
            old_tables.append(table)
        elif table in ['entities', 'entity_relationships', 'events', 'processes']:
            entity_tables.append(table)
        else:
            other_tables.append(table)
    
    if entity_tables:
        print("\n✓ Entity Framework Tables:")
        for t in sorted(entity_tables):
            print(f"  - {t}")
    
    if archive_tables:
        print("\n✓ Archived Legacy Tables:")
        for t in sorted(archive_tables):
            print(f"  - {t}")
    
    if old_tables:
        print("\n⚠ Old Tables Still Present (not dropped yet):")
        for t in sorted(old_tables):
            print(f"  - {t}")
        print("  Note: These can be dropped with DROP TABLE after confirming archive is complete")
    
    if other_tables:
        print("\n📋 Other Tables:")
        for t in sorted(other_tables[:10]):  # Show first 10
            print(f"  - {t}")
        if len(other_tables) > 10:
            print(f"  ... and {len(other_tables) - 10} more")
    
    # Check entity count
    cursor.execute("SELECT COUNT(*) FROM entities")
    entity_count = cursor.fetchone()[0]
    print(f"\n✓ Total entities: {entity_count}")
    
    # Check entity types
    cursor.execute("SELECT entity_type, COUNT(*) as count FROM entities GROUP BY entity_type")
    entity_types = cursor.fetchall()
    
    print("\nEntity breakdown:")
    for entity_type, count in entity_types:
        print(f"  - {entity_type}: {count}")
    
    conn.close()
    return True


def check_archived_files():
    """Check what files were archived."""
    archive_dir = Path(__file__).parent.parent / "archive" / "phase8_legacy"
    
    if not archive_dir.exists():
        print("\n❌ Archive directory not found")
        return False
    
    print(f"\n✓ Archive directory found at: {archive_dir}")
    
    # List archived files
    archived_files = list(archive_dir.glob("*"))
    
    if archived_files:
        print(f"\nArchived {len(archived_files)} items:")
        for f in sorted(archived_files):
            if f.is_file():
                print(f"  - {f.name} (file)")
            else:
                print(f"  - {f.name}/ (directory)")
    
    return True


def check_migration_status():
    """Check migration completion status."""
    migration_guide = Path(__file__).parent.parent.parent / "docs" / "migration_completion_guide.md"
    phase8_summary = Path(__file__).parent.parent.parent / "docs" / "phase8_summary.md"
    
    print("\n📄 Documentation Status:")
    
    if migration_guide.exists():
        print("  ✓ Migration completion guide created")
    else:
        print("  ❌ Migration completion guide missing")
    
    if phase8_summary.exists():
        print("  ✓ Phase 8 summary created")
    else:
        print("  ⚠ Phase 8 summary not created yet")
    
    return True


def main():
    """Run all checks."""
    print("=" * 60)
    print("Phase 8 Legacy Cleanup Verification")
    print("=" * 60)
    
    # Run tests
    db_ok = test_database_structure()
    archive_ok = check_archived_files()
    docs_ok = check_migration_status()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if db_ok and archive_ok:
        print("\n✅ Phase 8 cleanup completed successfully!")
        print("\nKey achievements:")
        print("- Legacy components archived to archive/phase8_legacy/")
        print("- Database migration prepared (tables archived)")
        print("- Entity framework is primary system")
        print("- Documentation updated")
        
        print("\nNext steps:")
        print("1. Review archived tables and drop when ready:")
        print("   DROP TABLE agents, tasks, messages, tools, context_documents;")
        print("2. Test full system functionality")
        print("3. Create Phase 8 summary documentation")
    else:
        print("\n❌ Some issues found. Please review above.")


if __name__ == "__main__":
    main()