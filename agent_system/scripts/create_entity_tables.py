#!/usr/bin/env python3
"""
Create the missing entity-specific tables (agents, tasks, tools, etc.)
that the EntityManager expects to exist alongside the entities table.
"""

import asyncio
import aiosqlite
from pathlib import Path

async def create_entity_tables():
    """Create all entity-specific tables required by EntityManager."""
    db_path = Path(__file__).parent.parent / "data" / "agent_system.db"
    
    async with aiosqlite.connect(db_path) as db:
        print("Creating entity-specific tables...")
        
        # Create agents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                instruction TEXT,
                context_documents TEXT DEFAULT '[]',
                available_tools TEXT DEFAULT '[]',
                permissions TEXT DEFAULT '[]',
                constraints TEXT DEFAULT '[]',
                FOREIGN KEY (id) REFERENCES entities(entity_id)
            )
        """)
        print("✅ Created agents table")
        
        # Create tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                parent_task_id INTEGER,
                tree_id INTEGER,
                agent_id INTEGER,
                instruction TEXT,
                status TEXT DEFAULT 'created',
                result TEXT DEFAULT '{}',
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (id) REFERENCES entities(entity_id)
            )
        """)
        print("✅ Created tasks table")
        
        # Create tools table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'system',
                implementation TEXT,
                parameters TEXT DEFAULT '{}',
                permissions TEXT DEFAULT '[]',
                FOREIGN KEY (id) REFERENCES entities(entity_id)
            )
        """)
        print("✅ Created tools table")
        
        # Create context_documents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS context_documents (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT,
                category TEXT DEFAULT 'general',
                content TEXT,
                format TEXT DEFAULT 'markdown',
                version TEXT DEFAULT '1.0.0',
                FOREIGN KEY (id) REFERENCES entities(entity_id)
            )
        """)
        print("✅ Created context_documents table")
        
        # Create processes table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                parameters TEXT DEFAULT '{}',
                steps TEXT DEFAULT '[]',
                rollback_steps TEXT DEFAULT '[]',
                permissions TEXT DEFAULT '[]',
                FOREIGN KEY (id) REFERENCES entities(entity_id)
            )
        """)
        print("✅ Created processes table")
        
        # Create messages table if it doesn't exist
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        print("✅ Created/verified messages table")
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_tree ON tasks(tree_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_context_name ON context_documents(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_context_category ON context_documents(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_task ON messages(task_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type)")
        print("✅ Created indexes")
        
        await db.commit()
        print("\n✅ All entity tables created successfully!")

async def check_existing_entities():
    """Check if there are any existing entities that need to be migrated."""
    db_path = Path(__file__).parent.parent / "data" / "agent_system.db"
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Check for entities without corresponding records in type-specific tables
        cursor = await db.execute("""
            SELECT entity_type, COUNT(*) as count 
            FROM entities 
            GROUP BY entity_type
        """)
        
        results = await cursor.fetchall()
        if results:
            print("\nExisting entities in database:")
            for row in results:
                print(f"  - {row['entity_type']}: {row['count']} entities")
            
            # Check for orphaned agent entities
            cursor = await db.execute("""
                SELECT e.entity_id, e.name 
                FROM entities e
                LEFT JOIN agents a ON e.entity_id = a.id
                WHERE e.entity_type = 'agent' AND a.id IS NULL
            """)
            orphaned_agents = await cursor.fetchall()
            
            if orphaned_agents:
                print(f"\n⚠️  Found {len(orphaned_agents)} agent entities without agent records")
                print("   These will need to be migrated or recreated")

async def main():
    """Main function to create entity tables."""
    print("Entity Table Creation Script")
    print("===========================\n")
    
    try:
        await create_entity_tables()
        await check_existing_entities()
        
        print("\n✅ Entity table creation completed successfully!")
        print("\nNext steps:")
        print("1. Run the system initialization script to populate the tables")
        print("2. Or manually migrate existing entity data if needed")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())