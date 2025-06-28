"""Common database operations for entity managers."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import aiosqlite

from agent_system.core.events.event_types import EntityType


class DatabaseOperations:
    """Helper class for common database operations."""
    
    @staticmethod
    async def insert_entity_record(
        db, 
        entity_type: EntityType, 
        name: str, 
        **kwargs
    ) -> int:
        """Insert base entity record and return entity_id."""
        cursor = await db.execute("""
            INSERT INTO entities (entity_type, entity_id, name, version, state, metadata, created_at, updated_at)
            VALUES (?, (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = ?), ?, ?, ?, ?, ?, ?)
        """, (
            entity_type.value,
            entity_type.value,
            name,
            kwargs.get('version', '1.0.0'),
            kwargs.get('state', 'active'),
            json.dumps(kwargs.get('metadata', {})),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        return cursor.lastrowid
    
    @staticmethod
    async def get_entity_record(
        db,
        entity_type: EntityType,
        entity_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get base entity record."""
        cursor = await db.execute("""
            SELECT * FROM entities 
            WHERE entity_type = ? AND entity_id = ?
        """, (entity_type.value, entity_id))
        
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            data['metadata'] = json.loads(data.get('metadata', '{}'))
            return data
        return None
    
    @staticmethod
    async def update_entity_record(
        db,
        entity_type: EntityType,
        entity_id: int,
        **updates
    ):
        """Update base entity record."""
        await db.execute("""
            UPDATE entities 
            SET name = ?, version = ?, state = ?, metadata = ?, updated_at = ?
            WHERE entity_type = ? AND entity_id = ?
        """, (
            updates.get('name'),
            updates.get('version'),
            updates.get('state'),
            json.dumps(updates.get('metadata', {})),
            datetime.now().isoformat(),
            entity_type.value,
            entity_id
        ))
    
    @staticmethod
    async def delete_entity_record(
        db,
        entity_type: EntityType,
        entity_id: int
    ):
        """Delete base entity record."""
        await db.execute("""
            DELETE FROM entities 
            WHERE entity_type = ? AND entity_id = ?
        """, (entity_type.value, entity_id))
    
    @staticmethod
    async def get_entity_relationships(
        db,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, List[int]]:
        """Get all relationships for an entity."""
        cursor = await db.execute("""
            SELECT relationship_type, target_id
            FROM entity_relationships
            WHERE source_type = ? AND source_id = ?
        """, (entity_type.value, entity_id))
        
        rows = await cursor.fetchall()
        relationships = {}
        
        for row in rows:
            rel_type = row['relationship_type']
            if rel_type not in relationships:
                relationships[rel_type] = []
            relationships[rel_type].append(row['target_id'])
        
        return relationships
    
    @staticmethod
    async def delete_entity_relationships(
        db,
        entity_type: EntityType,
        entity_id: int
    ):
        """Delete all relationships for an entity."""
        await db.execute("""
            DELETE FROM entity_relationships 
            WHERE (source_type = ? AND source_id = ?) 
               OR (target_type = ? AND target_id = ?)
        """, (entity_type.value, entity_id, entity_type.value, entity_id))