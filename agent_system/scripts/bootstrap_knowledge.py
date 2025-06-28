#!/usr/bin/env python3
"""
Bootstrap Knowledge System

Converts existing documentation into structured knowledge entities
and sets up the MVP knowledge system.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.knowledge.bootstrap import bootstrap_knowledge_system
from core.knowledge.storage import KnowledgeStorage
from core.knowledge.engine import ContextAssemblyEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_knowledge_system() -> None:
    """Test the knowledge system after bootstrap."""
    logger.info("\nTesting knowledge system...")
    
    storage = KnowledgeStorage()
    engine = ContextAssemblyEngine(storage)
    
    # Test 1: Context assembly for planning agent
    logger.info("\nTest 1: Planning agent context assembly")
    test_context = engine.assemble_context_for_task(
        "Plan a software development project with multiple components",
        "planning_agent"
    )
    
    logger.info(f"Context completeness: {test_context.completeness_score:.2f}")
    logger.info(f"Context sources: {len(test_context.knowledge_sources)}")
    logger.info(f"Domain identified: {test_context.domain}")
    
    if test_context.missing_requirements:
        logger.warning(f"Missing requirements: {test_context.missing_requirements}")
    
    # Test 2: Context assembly for process discovery
    logger.info("\nTest 2: Process discovery context assembly")
    test_context2 = engine.assemble_context_for_task(
        "Analyze and establish processes for a new data pipeline system",
        "process_discovery"
    )
    
    logger.info(f"Context completeness: {test_context2.completeness_score:.2f}")
    logger.info(f"Context sources: {len(test_context2.knowledge_sources)}")
    
    # Test 3: Knowledge gap detection
    logger.info("\nTest 3: Knowledge gap detection")
    gaps = engine.identify_knowledge_gaps(
        "Build a machine learning model for prediction",
        "investigator_agent"
    )
    
    if gaps:
        logger.info(f"Identified {len(gaps)} knowledge gaps:")
        for gap in gaps:
            logger.info(f"  - {gap.gap_type}: {gap.description}")
    else:
        logger.info("No knowledge gaps identified")
    
    # Test 4: Knowledge statistics
    logger.info("\nTest 4: Knowledge base statistics")
    stats = storage.get_statistics()
    logger.info(f"Total entities: {stats['total_entities']}")
    logger.info(f"By type: {stats['entities_by_type']}")
    logger.info(f"By domain: {stats['entities_by_domain']}")
    
    # Test 5: Relationship validation
    logger.info("\nTest 5: Relationship validation")
    missing_rels = storage.validate_relationships()
    if missing_rels:
        logger.warning(f"Found {len(missing_rels)} entities with missing relationships:")
        for entity_id, missing in list(missing_rels.items())[:5]:  # Show first 5
            logger.warning(f"  - {entity_id}: {missing}")
    else:
        logger.info("All relationships valid")


def main() -> None:
    """Main bootstrap function."""
    logger.info("=== Knowledge System Bootstrap ===")
    logger.info("Starting knowledge system bootstrap...")
    
    # Check if knowledge directory already exists and has content
    knowledge_dir = Path("knowledge")
    if knowledge_dir.exists() and any(knowledge_dir.iterdir()):
        logger.warning("Knowledge directory already exists and contains files.")
        response = input("Do you want to rebuild the knowledge base? (y/N): ")
        if response.lower() != 'y':
            logger.info("Bootstrap cancelled.")
            return
    
    # Run the bootstrap conversion
    try:
        results = bootstrap_knowledge_system(
            docs_dir=".",  # Current directory (agent_system)
            knowledge_dir="knowledge"
        )
        
        logger.info("\n=== Bootstrap Results ===")
        logger.info(f"Successfully converted: {results['converted']} entities")
        
        if results['failed'] > 0:
            logger.warning(f"Failed conversions: {results['failed']}")
            logger.warning(f"Failed files: {results['failed_files']}")
        
        # Run tests
        test_knowledge_system()
        
        logger.info("\n=== Knowledge System Ready ===")
        logger.info("The MVP knowledge system has been successfully bootstrapped!")
        logger.info("Knowledge entities are stored in: knowledge/")
        logger.info("\nNext steps:")
        logger.info("1. Run system initialization tasks to establish frameworks")
        logger.info("2. Test context assembly with real tasks")
        logger.info("3. Monitor knowledge evolution through usage")
        
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()