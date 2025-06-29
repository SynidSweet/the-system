"""
Performance and efficiency tests for the agent system.

Tests system performance metrics against defined thresholds.
"""

import time
import psutil
import uuid
from typing import List

from .test_utils import SuiteResults, PerformanceMonitor
from agent_system.core.events.event_types import EntityType


class PerformanceTests:
    """Performance and efficiency test suite"""
    
    def __init__(self, database, entity_manager):
        self.database = database
        self.entity_manager = entity_manager
        self.results = SuiteResults("Performance")
        self.monitor = PerformanceMonitor()
    
    async def run_all(self) -> SuiteResults:
        """Run all performance tests"""
        # Database query performance
        await self.results.run_test(
            "Database Query Performance",
            lambda: self._test_database_performance()
        )
        
        # Entity creation performance
        await self.results.run_test(
            "Entity Creation Performance",
            lambda: self._test_entity_creation_performance()
        )
        
        # Memory usage
        await self.results.run_test(
            "Memory Usage",
            lambda: self._test_memory_usage()
        )
        
        # Concurrent operations
        await self.results.run_test(
            "Concurrent Operations",
            lambda: self._test_concurrent_operations()
        )
        
        # Cache effectiveness
        await self.results.run_test(
            "Cache Effectiveness",
            lambda: self._test_cache_performance()
        )
        
        return self.results
    
    async def _test_database_performance(self) -> None:
        """Test database query performance"""
        # Test simple query performance
        async def simple_query():
            await self.database.agents.get_all_active()
        
        result = await self.monitor.measure(
            "Simple Agent Query",
            simple_query,
            threshold=0.1  # 100ms threshold
        )
        assert result["passed"], result["message"]
        
        # Test complex query performance
        async def complex_query():
            # Get all tasks with their relationships
            tasks = await self.entity_manager.list_entities(EntityType.TASK)
            for task in tasks[:10]:  # Limit to prevent test slowdown
                await self.entity_manager.get_entity_relationships(
                    task.entity_id, "depends_on"
                )
        
        result = await self.monitor.measure(
            "Complex Task Query",
            complex_query,
            threshold=1.0  # 1 second threshold
        )
        assert result["passed"], result["message"]
    
    async def _test_entity_creation_performance(self) -> None:
        """Test entity creation performance"""
        # Single entity creation
        async def create_single():
            await self.entity_manager.create_entity(
                EntityType.TASK,
                name=f"perf_test_{uuid.uuid4().hex[:8]}",
                instruction="Performance test task"
            )
        
        result = await self.monitor.measure(
            "Single Entity Creation",
            create_single,
            threshold=0.05  # 50ms threshold
        )
        assert result["passed"], result["message"]
        
        # Bulk entity creation
        async def create_bulk():
            tasks = []
            for i in range(10):
                task = await self.entity_manager.create_entity(
                    EntityType.TASK,
                    name=f"bulk_test_{i}_{uuid.uuid4().hex[:8]}",
                    instruction=f"Bulk test task {i}"
                )
                tasks.append(task)
            return tasks
        
        result = await self.monitor.measure(
            "Bulk Entity Creation (10)",
            create_bulk,
            threshold=0.5  # 500ms threshold for 10 entities
        )
        assert result["passed"], result["message"]
    
    async def _test_memory_usage(self) -> None:
        """Test memory usage stays within bounds"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        entities = []
        for i in range(100):
            entity = await self.entity_manager.create_entity(
                EntityType.CONTEXT,
                name=f"memory_test_{i}",
                content="x" * 1000  # 1KB of content
            )
            entities.append(entity)
        
        # Check memory increase
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Allow up to 50MB increase for 100 entities
        assert memory_increase < 50, \
            f"Memory usage increased by {memory_increase:.1f}MB (limit: 50MB)"
        
        # Cleanup
        for entity in entities:
            await self.entity_manager.update_entity(
                EntityType.CONTEXT,
                entity.entity_id,
                {"state": "inactive"}
            )
    
    async def _test_concurrent_operations(self) -> None:
        """Test performance under concurrent load"""
        import asyncio
        
        async def concurrent_operation(index: int):
            """Single concurrent operation"""
            agent = await self.entity_manager.create_entity(
                EntityType.AGENT,
                name=f"concurrent_test_{index}_{uuid.uuid4().hex[:8]}",
                instruction=f"Concurrent test agent {index}"
            )
            
            # Perform some operations
            await self.entity_manager.get_entity(EntityType.AGENT, agent.entity_id)
            await self.entity_manager.update_entity(
                EntityType.AGENT,
                agent.entity_id,
                {"instruction": f"Updated {index}"}
            )
            
            return agent
        
        # Run 20 concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        assert len(results) == 20, "Not all concurrent operations completed"
        assert duration < 2.0, f"Concurrent operations too slow: {duration:.2f}s"
        
        # Cleanup
        for agent in results:
            await self.entity_manager.update_entity(
                EntityType.AGENT,
                agent.entity_id,
                {"state": "inactive"}
            )
    
    async def _test_cache_performance(self) -> None:
        """Test caching effectiveness"""
        # Create test entity
        test_agent = await self.entity_manager.create_entity(
            EntityType.AGENT,
            name=f"cache_test_{uuid.uuid4().hex[:8]}",
            instruction="Cache test agent"
        )
        
        # First access (cache miss)
        start = time.time()
        await self.entity_manager.get_entity(EntityType.AGENT, test_agent.entity_id)
        first_access = time.time() - start
        
        # Second access (should be cached)
        start = time.time()
        await self.entity_manager.get_entity(EntityType.AGENT, test_agent.entity_id)
        second_access = time.time() - start
        
        # Cache should make second access at least 50% faster
        improvement = (first_access - second_access) / first_access
        assert improvement > 0.5 or second_access < 0.001, \
            f"Cache not effective: {improvement:.1%} improvement (expected >50%)"
        
        # Test cache with relationships
        await self.entity_manager.add_entity_relationship(
            test_agent.entity_id, "uses", test_agent.entity_id
        )
        
        # First relationship query
        start = time.time()
        await self.entity_manager.get_entity_relationships(
            test_agent.entity_id, "uses"
        )
        first_rel = time.time() - start
        
        # Second relationship query (cached)
        start = time.time()
        await self.entity_manager.get_entity_relationships(
            test_agent.entity_id, "uses"
        )
        second_rel = time.time() - start
        
        rel_improvement = (first_rel - second_rel) / first_rel if first_rel > 0 else 1
        assert rel_improvement > 0.5 or second_rel < 0.001, \
            f"Relationship cache not effective: {rel_improvement:.1%} improvement"