#!/usr/bin/env python3
"""
Migrate existing task entities to the tasks table.
"""

import sqlite3
import json
from pathlib import Path

def migrate_tasks():
    """Migrate task entities to tasks table."""
    db_path = Path(__file__).parent.parent / "data" / "agent_system.db"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get all task entities without corresponding task records
        cursor.execute("""
            SELECT e.entity_id, e.name, e.metadata
            FROM entities e 
            WHERE e.entity_type = 'task' 
            AND NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id = e.entity_id)
        """)
        
        tasks_to_migrate = cursor.fetchall()
        
        if not tasks_to_migrate:
            print("No tasks to migrate")
            return
        
        print(f"Migrating {len(tasks_to_migrate)} tasks...")
        
        for row in tasks_to_migrate:
            entity_id = row['entity_id']
            name = row['name']
            metadata = json.loads(row['metadata'] or '{}')
            
            # Extract task data from metadata
            instruction = metadata.get('instruction', name)
            parent_task_id = metadata.get('parent_task_id')
            tree_id = metadata.get('tree_id', entity_id)  # Use entity_id as tree_id if not set
            agent_id = metadata.get('agent_id')
            status = metadata.get('status', 'created')
            result = metadata.get('result', {})
            
            cursor.execute("""
                INSERT INTO tasks (id, parent_task_id, tree_id, agent_id, instruction, status, result, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                parent_task_id,
                tree_id,
                agent_id,
                instruction,
                status,
                json.dumps(result),
                json.dumps(metadata)
            ))
            
            print(f"✅ Migrated task: {name} (ID: {entity_id})")
        
        conn.commit()
        print(f"\n✅ Successfully migrated {len(tasks_to_migrate)} tasks")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tasks()