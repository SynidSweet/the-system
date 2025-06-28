# Seed Configuration Documentation

This directory contains YAML configuration files that define the system's initial state when seeding. The configuration-driven approach separates data from execution logic, making the system more maintainable and easier to modify.

## Configuration Files

### `agents.yaml`
Defines all agent configurations including:
- **name**: Unique agent identifier
- **instruction**: Detailed agent instructions and behavior
- **context_documents**: List of context documents the agent should have access to
- **available_tools**: List of tools the agent can use
- **permissions**: Agent permission settings (web_search, file_system, etc.)

### `tools.yaml`  
Defines all tool configurations including:
- **name**: Unique tool identifier
- **description**: Tool purpose and functionality
- **category**: Tool category (system, core, etc.)
- **implementation**: Implementation details (type, module_path, class_name)
- **parameters**: Tool parameter schema
- **permissions**: Required permissions for tool usage

### `documents.yaml`
Defines all context document configurations including:
- **filesystem_docs**: Auto-load documents from directory patterns
- **agent_guides**: Agent-specific guide documents loaded from files
- **system_references**: System reference documents with inline content

## Configuration Validation

The configuration loader automatically validates:
- YAML syntax and structure
- Required fields and data types  
- File path existence for referenced documents
- Agent permission consistency
- Tool implementation validity

## Usage

The seeding system automatically loads and validates configuration:

```python
from scripts.seeders import load_configuration, SystemSeeder

# Load configuration
config = load_configuration("config/seeds")

# Seed system with configuration
seeder = SystemSeeder(database, "config/seeds")
await seeder.seed_all()
```

## Modifying Configuration

### Adding a New Agent
1. Add agent definition to `agents.yaml`
2. Create any required context documents
3. Ensure referenced tools exist
4. Run seeding to validate

### Adding a New Tool
1. Add tool definition to `tools.yaml`  
2. Implement tool class if needed
3. Update agent configurations to reference tool
4. Run seeding to validate

### Adding Context Documents
1. For file-based: Place file in docs directory (auto-discovered)
2. For agent guides: Add to `agent_guides` section with file_path
3. For system references: Add to `system_references` with inline content

## Architecture Benefits

### Separation of Concerns
- **Configuration**: Pure data in YAML files
- **Logic**: Execution code in seeder classes
- **Validation**: Comprehensive validation in config loader

### Maintainability
- Easy to modify without touching code
- Version control friendly
- Clear dependency tracking
- Modular seeder architecture

### Reliability
- Configuration validation before execution
- Type safety with Pydantic models
- Comprehensive error handling
- Rollback capability through version control

## Migration from Legacy

The legacy `seed_system_legacy.py` file contained 1,228 lines with hardcoded configuration. The refactored approach:

- **87% line reduction**: From 1,228 to 161 lines
- **Configuration extraction**: All hardcoded data moved to YAML
- **Modular architecture**: Separate seeder classes by entity type
- **Improved validation**: Comprehensive error checking and reporting
- **Better maintainability**: Easy to modify configuration without code changes

## Error Handling

The configuration system provides detailed error messages for:
- Missing configuration files
- Invalid YAML syntax
- Missing required fields
- Invalid file paths
- Type validation errors
- Dependency validation issues

## Future Enhancements

The configuration system is designed to support:
- Environment-specific configurations
- Configuration templates and inheritance
- Dynamic configuration reloading
- Configuration migration utilities
- Advanced validation rules