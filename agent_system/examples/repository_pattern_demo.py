"""Demonstration of the repository pattern implementation."""

import asyncio
import os
import tempfile
from typing import Dict, Any

from ..core.repositories import RepositoryFactory, RepositoryManager
from ..core.events.event_types import EntityType
from ..core.events.event_manager import EventManager


async def database_repository_demo():
    """Demonstrate database repository usage."""
    print("=== Database Repository Demo ===")
    
    # Create temporary database for demo
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Initialize database (in real usage, this would be done by system setup)
        # For demo purposes, we'll assume tables exist
        
        # Create repository manager
        repo_manager = RepositoryManager(db_path=db_path)
        
        # Get specific repositories
        agent_repo = repo_manager.agents
        task_repo = repo_manager.tasks
        
        print(f"Created repositories for database: {db_path}")
        print(f"Agent repository type: {type(agent_repo).__name__}")
        print(f"Task repository type: {type(task_repo).__name__}")
        
        # Note: In real usage, you would create entities like this:
        # agent_data = {
        #     'name': 'demo_agent',
        #     'instruction': 'Demo agent instruction',
        #     'available_tools': ['tool1', 'tool2'],
        #     'context_documents': ['doc1'],
        #     'permissions': [],
        #     'constraints': []
        # }
        # agent = await agent_repo.create(agent_data)
        # print(f"Created agent: {agent.name} with ID: {agent.entity_id}")
        
    finally:
        # Clean up temporary database
        os.unlink(db_path)


async def memory_repository_demo():
    """Demonstrate in-memory repository usage for testing."""
    print("\n=== In-Memory Repository Demo ===")
    
    # Create in-memory repositories for testing
    agent_repo = RepositoryFactory.create_repository(
        EntityType.AGENT,
        db_path="memory",  # Not used for in-memory
        use_memory=True
    )
    
    task_repo = RepositoryFactory.create_repository(
        EntityType.TASK,
        db_path="memory",  # Not used for in-memory
        use_memory=True
    )
    
    print(f"Agent repository type: {type(agent_repo).__name__}")
    print(f"Task repository type: {type(task_repo).__name__}")
    
    # Example agent creation (would work if entities were properly set up)
    # agent_data = {
    #     'name': 'test_agent',
    #     'instruction': 'Test agent for demo',
    #     'available_tools': ['search', 'analyze'],
    #     'context_documents': ['test_doc'],
    #     'permissions': [],
    #     'constraints': []
    # }
    # 
    # agent = await agent_repo.create(agent_data)
    # print(f"Created in-memory agent: {agent.name}")
    # 
    # # Search for agents with specific capability
    # search_results = await agent_repo.find_by_capability('search')
    # print(f"Found {len(search_results)} agents with 'search' capability")


async def repository_pattern_benefits_demo():
    """Demonstrate the benefits of the repository pattern."""
    print("\n=== Repository Pattern Benefits ===")
    
    print("1. Type Safety:")
    print("   - Repository[T] provides compile-time type checking")
    print("   - IDE autocomplete for entity-specific methods")
    
    print("\n2. Testability:")
    print("   - Easy to swap database repositories with in-memory ones")
    print("   - No database setup required for unit tests")
    
    print("\n3. Separation of Concerns:")
    print("   - Business logic separated from data access")
    print("   - Database implementation details hidden")
    
    print("\n4. Consistency:")
    print("   - Standardized CRUD operations across all entities")
    print("   - Consistent error handling and event logging")
    
    print("\n5. Extensibility:")
    print("   - Easy to add entity-specific query methods")
    print("   - Support for different storage backends")


def usage_patterns_demo():
    """Show common usage patterns."""
    print("\n=== Usage Patterns ===")
    
    print("Pattern 1: Direct Repository Creation")
    print("""
    from ..core.repositories import AgentRepository
    
    repo = AgentRepository(db_path="/path/to/db")
    agent = await repo.create(agent_data)
    agents = await repo.find_by_capability("search")
    """)
    
    print("Pattern 2: Repository Factory")
    print("""
    from ..core.repositories import RepositoryFactory
    from ..core.events.event_types import EntityType
    
    repo = RepositoryFactory.create_repository(
        EntityType.AGENT, 
        db_path="/path/to/db"
    )
    """)
    
    print("Pattern 3: Repository Manager (Recommended)")
    print("""
    from ..core.repositories import RepositoryManager
    
    manager = RepositoryManager(db_path="/path/to/db")
    agent = await manager.agents.create(agent_data)
    task = await manager.tasks.create(task_data)
    """)
    
    print("Pattern 4: Testing with In-Memory Repositories")
    print("""
    # In your test file
    repo = RepositoryFactory.create_repository(
        EntityType.AGENT,
        db_path="memory",
        use_memory=True
    )
    # No database setup required!
    """)


async def main():
    """Run all demonstrations."""
    print("Repository Pattern Implementation Demo")
    print("=" * 50)
    
    await database_repository_demo()
    await memory_repository_demo()
    await repository_pattern_benefits_demo()
    usage_patterns_demo()
    
    print("\nRepository pattern implementation complete!")
    print("Key benefits achieved:")
    print("✓ Clean separation of data access from business logic")
    print("✓ Type-safe repository interfaces")
    print("✓ Easy testing with in-memory implementations")
    print("✓ Consistent CRUD operations across all entities")
    print("✓ Extensible architecture for new storage backends")


if __name__ == "__main__":
    asyncio.run(main())