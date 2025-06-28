# CLAUDE.md - Database Layer

## Module Overview

The database module provides the persistence layer for The System's entity-based architecture. It uses SQLite with SQLModel ORM for type-safe database operations, migration management for schema evolution, and connection pooling for performance. The database stores all 6 entity types with proper relationships and constraints.

## Key Components

- **config/database.py**: Database connection management and configuration
- **migrations/**: SQL migration files for schema evolution and updates
- **Entity Tables**: 6 core tables (agents, tasks, tools, context_documents, processes, events)
- **Relationship Management**: Foreign key constraints and referential integrity
- **Connection Pooling**: Async SQLite with proper connection lifecycle

## Database Schema

### Core Entity Tables
- **agents**: Agent definitions with instructions, tools, and permissions
- **tasks**: Task execution state with tree structure and metadata
- **tools**: Tool definitions with MCP integration and permissions
- **context_documents**: Knowledge documents with categories and versioning
- **processes**: Process frameworks with triggers and requirements
- **events**: System events for tracking and optimization

### Key Relationships
- Tasks → Agents (execution assignment)
- Tasks → Tasks (parent/child tree structure)
- Agents → Tools (many-to-many through permissions)
- Events → All entities (tracking and audit trail)
- Processes → Tasks (framework establishment)

## Common Tasks

### Adding Database Migration
1. Create new migration file in `migrations/` with incremental number
2. Write SQL DDL statements for schema changes
3. Include both forward and rollback operations
4. Test migration on copy of production data
5. Update entity models to match new schema

### Querying Entities
1. Use EntityManager facade for all database operations
2. Access type-specific managers via properties
3. Use async/await patterns for all database calls
4. Handle database exceptions appropriately
5. Ensure proper connection cleanup

### Managing Relationships
1. Define foreign key constraints in migration files
2. Use entity manager methods for relationship queries
3. Maintain referential integrity through proper deletion cascades
4. Test relationship constraints with various scenarios
5. Document relationship patterns and dependencies

### Performance Optimization
1. Add database indexes for frequently queried columns
2. Use connection pooling for concurrent operations
3. Implement query result caching where appropriate
4. Monitor query performance and optimize slow queries
5. Use database EXPLAIN plans for query analysis

## Architecture & Patterns

- **Entity-Based Design**: 6 fundamental entity types with proper relationships
- **Migration Management**: Incremental schema evolution with version control
- **Type Safety**: SQLModel ORM provides compile-time type checking
- **Async Operations**: All database operations use async/await patterns
- **Connection Management**: Proper connection lifecycle and cleanup
- **Transaction Support**: ACID compliance for critical operations

## Testing

### Entity CRUD Testing
```python
# Test entity creation and retrieval
async with DatabaseManager() as db:
    entity_manager = EntityManager(db)
    agent = await entity_manager.agents.create({
        "name": "test_agent",
        "instruction": "Test instruction"
    })
    retrieved = await entity_manager.agents.get_by_id(agent.id)
    assert retrieved.name == "test_agent"
```

### Migration Testing
```python
# Test migration execution
from agent_system.database.migrations import run_migrations
await run_migrations(db_path, target_version=15)
# Verify schema changes
```

### Relationship Testing
```python
# Test entity relationships
task = await entity_manager.tasks.create({...})
agent = await entity_manager.agents.get_by_id(task.agent_id)
assert agent is not None
```

## Performance Considerations

- **Connection Pooling**: Async SQLite with proper connection management
- **Index Strategy**: Strategic indexes on frequently queried columns
- **Query Optimization**: Efficient queries with proper joins and filtering
- **Transaction Management**: Minimal transaction scope for consistency
- **Result Caching**: Cache frequently accessed data for performance

## Gotchas & Tips

### Database Design
- Always use migrations for schema changes - never modify tables directly
- Define proper foreign key constraints for data integrity
- Use appropriate column types and constraints
- Add indexes for performance but avoid over-indexing
- Test migrations on realistic data volumes

### Entity Management
- Always use EntityManager facade rather than direct database access
- Use type-specific managers for entity operations
- Handle database exceptions appropriately with try/catch
- Ensure proper async/await usage for all database calls
- Clean up database connections in finally blocks

### Migration Management
- Number migrations incrementally for proper ordering
- Include both forward and rollback SQL statements
- Test migrations on copy of production data
- Document breaking changes and migration requirements
- Keep migrations focused and atomic

### Performance Optimization
- Use EXPLAIN QUERY PLAN to analyze slow queries
- Add indexes for frequently used WHERE clauses
- Avoid N+1 query patterns with proper joins
- Use connection pooling for concurrent operations
- Monitor database performance metrics

### Data Integrity
- Define proper foreign key constraints
- Use transactions for related operations
- Implement proper cascade deletion rules
- Validate data at application layer as well
- Monitor for orphaned records and data inconsistencies

## Integration Points

- **Entity Manager**: Primary interface for all database operations
- **API Layer**: Database operations through entity manager facade
- **Event System**: Database events tracked for optimization
- **Knowledge System**: Context documents stored and retrieved
- **Tool System**: Tool definitions and permissions managed

## Common Patterns

### Entity Creation Pattern
```python
async def create_entity_with_relations(data: Dict[str, Any]) -> EntityType:
    async with DatabaseManager() as db:
        entity_manager = EntityManager(db)
        
        # Create primary entity
        entity = await entity_manager.entities.create(data)
        
        # Create related entities
        for relation_data in data.get('relations', []):
            await entity_manager.relations.create({
                'entity_id': entity.id,
                **relation_data
            })
        
        return entity
```

### Transaction Pattern
```python
async def atomic_operation(db: DatabaseManager):
    async with db.transaction():
        # Multiple operations that must succeed together
        entity1 = await entity_manager.create(...)
        entity2 = await entity_manager.create(...)
        await entity_manager.update(entity1.id, ...)
        # All operations committed together
```

### Migration Pattern
```sql
-- Migration file: 016_add_feature.sql
-- Forward migration
ALTER TABLE agents ADD COLUMN new_field TEXT;
CREATE INDEX idx_agents_new_field ON agents(new_field);

-- Rollback migration (in separate section)
-- DROP INDEX idx_agents_new_field;
-- ALTER TABLE agents DROP COLUMN new_field;
```

### Query Optimization Pattern
```python
async def efficient_query(entity_manager: EntityManager) -> List[Entity]:
    # Use specific manager methods for optimized queries
    return await entity_manager.agents.find_by_capability_with_tools(
        capability="web_search",
        include_tools=True  # Single query with JOIN
    )
```

### Connection Management Pattern
```python
@asynccontextmanager
async def get_database_connection():
    db = DatabaseManager()
    try:
        await db.connect()
        yield db
    finally:
        await db.disconnect()
```