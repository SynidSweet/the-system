#!/usr/bin/env python3
"""
Database Migration Runner for Entity Framework
Phase 1: Database Foundation
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Get database path directly
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'agent_system', 'data', 'agent_system.db')


class MigrationRunner:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent
        
    def get_applied_migrations(self, conn) -> set:
        """Get list of already applied migrations"""
        cursor = conn.cursor()
        
        # Create migrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}
    
    def get_migration_files(self) -> list:
        """Get all migration files in order"""
        migrations = []
        for file in self.migrations_dir.glob("*.sql"):
            if file.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                migrations.append(file)
        return sorted(migrations)
    
    def apply_migration(self, conn, migration_file: Path):
        """Apply a single migration file"""
        version = migration_file.stem
        
        print(f"Applying migration: {version}")
        
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cursor = conn.cursor()
        try:
            # Use executescript for multiple statements
            cursor.executescript(migration_sql)
            
            # Record migration as applied
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,)
            )
            
            conn.commit()
            print(f"✓ Migration {version} applied successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error applying migration {version}: {e}")
            raise
    
    def run(self):
        """Run all pending migrations"""
        print(f"Running migrations on database: {self.db_path}")
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Get applied migrations
            applied = self.get_applied_migrations(conn)
            
            # Get migration files
            migration_files = self.get_migration_files()
            
            # Apply pending migrations
            pending_count = 0
            for migration_file in migration_files:
                version = migration_file.stem
                if version not in applied:
                    self.apply_migration(conn, migration_file)
                    pending_count += 1
            
            if pending_count == 0:
                print("No pending migrations to apply")
            else:
                print(f"\n✓ Applied {pending_count} migration(s) successfully")
                
            # Verify new tables exist
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('entities', 'entity_relationships', 'processes', 'events', 'rolling_review_counters')
                ORDER BY name
            """)
            
            new_tables = [row[0] for row in cursor.fetchall()]
            if new_tables:
                print(f"\nNew tables created: {', '.join(new_tables)}")
            
        finally:
            conn.close()


def main():
    # Ensure database directory exists
    db_dir = Path(DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Run migrations
    runner = MigrationRunner(DATABASE_PATH)
    runner.run()


if __name__ == "__main__":
    main()