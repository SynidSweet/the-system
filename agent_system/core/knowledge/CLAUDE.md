# CLAUDE.md - Knowledge System

## Module Overview

The knowledge module implements the MVP Knowledge System that converts documentation into structured knowledge entities, assembles context packages for isolated task success, and detects knowledge gaps. It provides file-based JSON storage that can evolve into a graph database as complexity grows.

## Key Components

### Core System (Refactored 2025-06-28)
- **engine.py**: Main interface for context assembly (130 lines, 80% reduction)
- **models.py**: Core data structures (ContextPackage, ValidationResult, KnowledgeGap)
- **entity.py**: Knowledge entity definitions and data models
- **storage.py**: File-based JSON storage with search capabilities

### Modular Context Assembly (NEW 2025-06-28)
- **assembly/**: Modular components for context assembly and validation
  - **context_assembler.py**: Core context assembly logic (151 lines)
  - **gap_detector.py**: Validation and gap detection (215 lines)
  - **context_formatter.py**: Entity formatting for context (186 lines)
  - **analysis_utils.py**: Analysis and extraction utilities (128 lines)

### Documentation Conversion
- **bootstrap.py**: Orchestrates documentation conversion to knowledge entities
- **converters/**: Modular components for documentation transformation
  - **documentation_parser.py**: Finds and parses various documentation types
  - **entity_converter.py**: Creates knowledge entities from parsed content
  - **relationship_builder.py**: Builds and validates entity relationships
  - **extraction_utils.py**: Utility methods for content extraction

## Common Tasks

### Working with Modular Context Assembly (NEW 2025-06-28)

#### Direct Component Usage (Recommended)
```python
from core.knowledge.assembly import ContextAssembler, GapDetector, ContextFormatter

# Use components directly for specific needs
storage = KnowledgeStorage("knowledge/")
assembler = ContextAssembler(storage)
context_package = assembler.assemble_context_for_task(
    "Implement user authentication", 
    "planning_agent"
)

# Validate context completeness
gap_detector = GapDetector(storage)
validation = gap_detector.validate_context_completeness(entities, task, agent)

# Format entities for context
formatter = ContextFormatter()
context_text = formatter.build_context_text(entities, task, agent)
```

#### Legacy Interface (Backward Compatible)
```python
from core.knowledge.engine import ContextAssemblyEngine

# Original interface still works
storage = KnowledgeStorage("knowledge/")
engine = ContextAssemblyEngine(storage)
context_package = engine.assemble_context_for_task("task", "agent")
```

### Converting Documentation to Knowledge
```python
from agent_system.core.knowledge import bootstrap_knowledge_system

# Convert all documentation in project
stats = bootstrap_knowledge_system(
    docs_dir=".",
    knowledge_dir="knowledge"
)
print(f"Converted {stats['converted']} entities")
```

### Adding New Knowledge Entity Types
1. Define extraction logic in `converters/extraction_utils.py`
2. Create converter method in `converters/entity_converter.py`
3. Add parser logic in `converters/documentation_parser.py`
4. Update bootstrap orchestration in `bootstrap.py`
5. Test end-to-end conversion

### Extending Entity Relationships
1. Define relationship rules in `converters/relationship_builder.py`
2. Add relationship detection methods
3. Update validation logic
4. Test relationship graph generation

### Creating Custom Extractors
```python
# In extraction_utils.py
@staticmethod
def extract_custom_pattern(content: str) -> List[str]:
    """Extract custom patterns from content."""
    patterns = []
    # Custom extraction logic
    custom_pattern = r"Your pattern here"
    matches = re.findall(custom_pattern, content)
    # Process matches
    return patterns[:10]  # Limit results
```

## Architecture & Patterns

### Modular Assembly Architecture (NEW 2025-06-28)
The context assembly system uses a modular component architecture:
- **ContextAssembler**: Core logic for assembling context packages from knowledge entities
- **GapDetector**: Validates context completeness and identifies missing knowledge
- **ContextFormatter**: Formats knowledge entities into comprehensive context text
- **AnalysisUtils**: Analysis and extraction utilities for patterns and domain inference
- **Engine**: Main interface that coordinates components while maintaining backward compatibility

### Converter Architecture (Refactored 2025-06-28)
The bootstrap system uses a modular converter architecture:
- **Parser**: Locates and reads documentation files
- **Converter**: Transforms content into knowledge entities
- **Extractor**: Utility methods for pattern extraction
- **Builder**: Creates relationships between entities
- **Orchestrator**: Coordinates the conversion pipeline

### Storage Pattern
- JSON files organized by entity type in subdirectories
- In-memory caching for performance
- Lazy loading with on-demand parsing
- Clear path to graph database migration

### Knowledge Entity Structure
```json
{
  "id": "unique-identifier",
  "type": "agent|process|tool|pattern|domain|system",
  "name": "Human-readable name",
  "version": "1.0.0",
  "domain": "knowledge-domain",
  "content": {
    "summary": "Brief description",
    "core_concepts": ["concept1", "concept2"],
    "procedures": ["step1", "step2"],
    "examples": ["example1"],
    "quality_criteria": ["criterion1"],
    "common_pitfalls": ["pitfall1"]
  },
  "relationships": {
    "enables": ["entity-id-1"],
    "requires": ["entity-id-2"],
    "related": ["entity-id-3"]
  }
}
```

## Testing

### Test Documentation Conversion
```python
# Test specific converter
converter = EntityConverter()
entity = converter.create_agent_entity("test_agent", content)
assert entity.type == "agent"
assert entity.domain == "expected_domain"
```

### Test Relationship Building
```python
builder = RelationshipBuilder()
builder.add_entity(entity1)
builder.add_entity(entity2)
relationships = builder.build_all_relationships()
assert relationships > 0
```

## Performance Considerations

- **Converter Performance**: Each converter module handles specific entity types to minimize processing
- **Extraction Efficiency**: Regex patterns compiled once and reused
- **Relationship Building**: O(n²) for relationship detection, but runs once during bootstrap
- **Storage Caching**: Entities cached in memory after first load
- **Context Assembly**: Lazy loading prevents loading entire knowledge base

## Gotchas & Tips

### Documentation Parsing
- Parser looks for specific file patterns (e.g., `*_guide.md`, `*_process.py`)
- YAML frontmatter is extracted but simplified (not full YAML parsing)
- File encoding assumed to be UTF-8

### Entity Conversion
- Missing required fields (like "purpose") will skip entity creation
- Entity IDs must be unique across all types
- Timestamps use ISO format for consistency

### Relationship Building
- Circular dependencies are detected and warned
- Orphaned entities (no relationships) are flagged
- Relationship validation runs after all entities are created

### Bootstrap Process
- Creates ~40-60 entities from typical documentation
- Generates relationship graph JSON for visualization
- Failed conversions are logged but don't stop process

## Integration Points

- **Context Engine**: Uses knowledge entities for task context assembly
- **Gap Detection**: Identifies missing knowledge preventing task success
- **Agent Runtime**: Provides context packages for isolated execution
- **Bootstrap Scripts**: Converts docs on system initialization

## Common Patterns

### Adding New Documentation Source
```python
# In documentation_parser.py
def find_custom_docs(self) -> List[Path]:
    """Find custom documentation files."""
    custom_dir = self.docs_dir / "custom"
    if not custom_dir.exists():
        return []
    return list(custom_dir.glob("*.md"))
```

### Creating Domain-Specific Extractor
```python
# In entity_converter.py
def create_custom_entity(self, name: str, content: str) -> KnowledgeEntity:
    """Create custom knowledge entity."""
    # Extract domain-specific patterns
    concepts = self._extract_custom_concepts(content)
    # Build entity with domain logic
    return KnowledgeEntity(
        id=f"custom_{name}",
        type="custom",
        # ... rest of entity
    )
```

### Implementing Knowledge Evolution
```python
# Track usage and effectiveness
def track_knowledge_usage(entity_id: str, success: bool):
    """Track how effectively knowledge enables task success."""
    # Update usage statistics
    # Identify patterns in failures
    # Suggest knowledge improvements
```

## Debugging

- Check `bootstrap.log` for conversion details
- Review `failed_conversions` list for parsing errors
- Examine `relationship_graph.json` for connection issues
- Use `storage.get_statistics()` for storage metrics
- Enable DEBUG logging for detailed extraction info