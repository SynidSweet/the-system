# Knowledge Entity Format Specification

## Overview

This specification defines the JSON-based format for knowledge entities in the MVP system. The format is designed to be simple, extensible, and migration-ready for future graph database implementations.

## Core Entity Structure

### Base Knowledge Entity Schema
```json
{
  "id": "string - unique identifier using namespace_type_name pattern",
  "type": "enum - domain|process|agent|tool|pattern|system", 
  "name": "string - human readable name",
  "version": "string - semantic version (1.0.0)",
  "domain": "string - primary domain area this knowledge belongs to",
  "process_frameworks": ["array of process framework names this knowledge applies to"],
  "content": { /* content object defined by type */ },
  "relationships": { /* relationship object */ },
  "context_templates": { /* template object */ },
  "isolation_requirements": { /* isolation object */ },
  "metadata": { /* metadata object */ }
}
```

## Type-Specific Content Structures

### Domain Knowledge Entity
```json
{
  "id": "domain_software_development",
  "type": "domain",
  "name": "Software Development Domain",
  "version": "1.0.0", 
  "domain": "software_development",
  "process_frameworks": ["development_lifecycle", "code_review", "testing"],
  "content": {
    "summary": "Comprehensive domain covering software development practices, methodologies, and quality standards",
    "core_concepts": [
      "Software engineering principles",
      "Development lifecycle management", 
      "Code quality and maintainability",
      "Testing and validation strategies",
      "Deployment and operations"
    ],
    "procedures": [
      "Requirements analysis and specification",
      "Architecture and design processes",
      "Implementation and coding standards",
      "Testing and quality assurance", 
      "Deployment and maintenance procedures"
    ],
    "examples": [
      "Agile development workflow",
      "Code review process", 
      "Continuous integration pipeline",
      "Bug tracking and resolution"
    ],
    "quality_criteria": [
      "Code maintainability and readability",
      "Test coverage and quality",
      "Performance and scalability",
      "Security and reliability"
    ],
    "common_pitfalls": [
      "Insufficient requirements analysis",
      "Poor architecture planning",
      "Inadequate testing coverage",
      "Premature optimization"
    ]
  },
  "relationships": {
    "enables": ["agent_software_developer", "process_code_review", "tool_development_environment"],
    "requires": ["domain_system_architecture", "domain_project_management"], 
    "related": ["domain_quality_assurance", "domain_devops"]
  },
  "context_templates": {
    "task_context": "When working in software development domain: Follow established coding standards, ensure comprehensive testing, maintain clear documentation, and consider maintainability in all implementation decisions.",
    "agent_context": "Software development requires systematic approach to {development_phase} with focus on {quality_aspects} and adherence to {coding_standards}."
  },
  "isolation_requirements": {
    "minimum_context": [
      "coding_standards_reference",
      "project_architecture_overview", 
      "testing_framework_documentation",
      "development_environment_setup"
    ],
    "validation_criteria": [
      "Can complete development tasks independently",
      "Has access to necessary development tools",
      "Understands quality and testing requirements", 
      "Can follow established procedures without external guidance"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "effectiveness_score": 0.0,
    "source": "documentation_conversion",
    "tags": ["development", "engineering", "quality"],
    "priority": "high"
  }
}
```

### Agent Knowledge Entity
```json
{
  "id": "agent_planning_agent",
  "type": "agent", 
  "name": "Planning Agent Specialization",
  "version": "1.0.0",
  "domain": "task_decomposition",
  "process_frameworks": ["task_breakdown", "workflow_design", "coordination_planning"],
  "content": {
    "summary": "Specialized in breaking complex tasks into coordinated workflows using established process frameworks",
    "core_concepts": [
      "Think in workflow architectures, not linear steps",
      "Leverage historical success patterns", 
      "Design for process evolution",
      "Enable isolated task success through complete context"
    ],
    "procedures": [
      "Entity-aware problem analysis",
      "Process-integrated decomposition",
      "Entity relationship optimization",
      "Quality-integrated planning"
    ],
    "examples": [
      "Multi-phase project breakdown",
      "Parallel task coordination",
      "Dependency management",
      "Resource allocation planning"
    ],
    "quality_criteria": [
      "Decomposition effectiveness",
      "Process integration success", 
      "Coordination efficiency",
      "Pattern discovery and capture"
    ],
    "common_pitfalls": [
      "Over-decomposition leading to coordination overhead",
      "Insufficient dependency analysis",
      "Poor resource requirement estimation",
      "Inadequate context provision for subtasks"
    ]
  },
  "relationships": {
    "enables": ["task_complex_project_breakdown", "process_workflow_coordination"],
    "requires": ["domain_project_management", "tool_entity_manager", "context_planning_methodologies"],
    "related": ["agent_agent_selector", "agent_task_evaluator", "agent_feedback"]
  },
  "context_templates": {
    "task_context": "As planning agent: Analyze task complexity, identify systematic frameworks, break down into coordinated subtasks with clear dependencies and complete context for isolated success.",
    "agent_context": "Planning requires systematic approach to {task_complexity} using {framework_type} with focus on {coordination_aspects} and ensuring {isolation_requirements}."
  },
  "isolation_requirements": {
    "minimum_context": [
      "planning_methodologies_reference",
      "task_decomposition_patterns",
      "coordination_frameworks",
      "dependency_management_guide"
    ],
    "validation_criteria": [
      "Can analyze complex tasks independently",
      "Can create systematic breakdown plans", 
      "Can identify coordination requirements",
      "Can ensure subtask isolation capability"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T10:00:00Z", 
    "usage_count": 0,
    "effectiveness_score": 0.0,
    "source": "agent_guide_conversion",
    "specialization_level": "high",
    "coordination_capability": "expert"
  }
}
```

### Process Knowledge Entity
```json
{
  "id": "process_task_breakdown",
  "type": "process",
  "name": "Task Breakdown Process Framework", 
  "version": "1.0.0",
  "domain": "task_management",
  "process_frameworks": ["systematic_decomposition"],
  "content": {
    "summary": "Systematic framework for breaking complex tasks into manageable, coordinated subtasks with complete isolation context",
    "core_concepts": [
      "Systematic framework establishment before breakdown",
      "Complete context provision for isolated success",
      "Dependency management and coordination",
      "Process compliance validation"
    ],
    "procedures": [
      "Framework analysis and establishment",
      "Systematic breakdown planning", 
      "Framework-compliant subtask creation",
      "Dependency validation and management"
    ],
    "examples": [
      "Software development project breakdown",
      "Research project decomposition",
      "Content creation workflow design",
      "System improvement initiative planning"
    ],
    "quality_criteria": [
      "All subtasks can succeed in isolation",
      "Dependencies are clear and manageable",
      "Framework compliance maintained",
      "Coordination overhead minimized"
    ],
    "common_pitfalls": [
      "Breakdown without framework establishment",
      "Insufficient context for isolation",
      "Circular dependencies", 
      "Framework compliance violations"
    ]
  },
  "relationships": {
    "enables": ["agent_planning_agent", "task_complex_decomposition"],
    "requires": ["process_framework_establishment", "domain_task_management"],
    "related": ["process_quality_evaluation", "process_coordination_management"]
  },
  "context_templates": {
    "task_context": "When executing task breakdown: Establish systematic framework first, ensure complete context for each subtask, validate dependencies, confirm isolation capability.",
    "agent_context": "Task breakdown requires {framework_type} establishment with {isolation_level} context and {dependency_complexity} coordination."
  },
  "isolation_requirements": {
    "minimum_context": [
      "systematic_framework_guide",
      "task_breakdown_methodologies", 
      "dependency_management_procedures",
      "isolation_validation_criteria"
    ],
    "validation_criteria": [
      "Can establish systematic frameworks",
      "Can create isolated subtasks",
      "Can manage complex dependencies",
      "Can validate framework compliance"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "effectiveness_score": 0.0,
    "source": "process_architecture_extraction",
    "automation_potential": "high",
    "complexity_level": "moderate"
  }
}
```

### Tool Knowledge Entity
```json
{
  "id": "tool_entity_manager",
  "type": "tool",
  "name": "Entity Manager Tool",
  "version": "1.0.0", 
  "domain": "system_operation",
  "process_frameworks": ["entity_management", "data_operations"],
  "content": {
    "summary": "Core tool for CRUD operations on all entity types with permission validation and usage tracking",
    "core_concepts": [
      "Entity lifecycle management",
      "Relationship tracking",
      "Permission-based access control",
      "Usage analytics and optimization"
    ],
    "procedures": [
      "Entity creation and validation",
      "Relationship establishment and maintenance",
      "Permission checking and enforcement", 
      "Usage tracking and analysis"
    ],
    "examples": [
      "Creating new task entities",
      "Updating agent configurations",
      "Tracking entity relationships",
      "Analyzing entity usage patterns"
    ],
    "quality_criteria": [
      "Data consistency and integrity",
      "Permission enforcement accuracy",
      "Performance within acceptable limits",
      "Complete usage tracking"
    ],
    "common_pitfalls": [
      "Permission bypass attempts",
      "Relationship consistency violations",
      "Performance degradation with scale",
      "Incomplete usage tracking"
    ]
  },
  "relationships": {
    "enables": ["all_agents", "all_processes"],
    "requires": ["system_database", "permission_system"],
    "related": ["tool_event_logger", "tool_permission_manager"]
  },
  "context_templates": {
    "task_context": "When using entity manager: Ensure proper permissions, validate data consistency, track relationships correctly, log all operations for analysis.",
    "agent_context": "Entity management requires {permission_level} access for {operation_type} on {entity_types} with {validation_requirements}."
  },
  "isolation_requirements": {
    "minimum_context": [
      "entity_framework_reference",
      "permission_system_guide",
      "data_validation_procedures",
      "usage_tracking_requirements"
    ],
    "validation_criteria": [
      "Can perform entity operations correctly",
      "Understands permission requirements", 
      "Can validate data consistency",
      "Can interpret usage analytics"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "effectiveness_score": 0.0,
    "source": "tool_documentation_conversion",
    "permission_level": "core",
    "availability": "all_agents"
  }
}
```

### Pattern Knowledge Entity
```json
{
  "id": "pattern_successful_task_breakdown",
  "type": "pattern",
  "name": "Successful Task Breakdown Pattern",
  "version": "1.0.0",
  "domain": "task_execution",
  "process_frameworks": ["task_breakdown", "workflow_coordination"],
  "content": {
    "summary": "Proven pattern for breaking complex tasks into successful, coordinated subtasks with high completion rates",
    "core_concepts": [
      "Framework establishment before breakdown",
      "Complete context provision strategy",
      "Dependency minimization approach",
      "Validation and quality assurance integration"
    ],
    "procedures": [
      "Systematic framework analysis and establishment",
      "Context completeness validation before subtask creation",
      "Dependency graph optimization",
      "Quality checkpoint integration"
    ],
    "examples": [
      "Software feature development breakdown",
      "Research project decomposition",
      "Content creation pipeline design",
      "System integration project planning"
    ],
    "quality_criteria": [
      "95%+ subtask success rate",
      "Minimal coordination overhead",
      "Complete isolation capability",
      "Quality maintained throughout execution"
    ],
    "common_pitfalls": [
      "Skipping framework establishment phase",
      "Insufficient context provision",
      "Over-complex dependency structures",
      "Missing quality validation steps"
    ]
  },
  "relationships": {
    "enables": ["process_task_breakdown", "agent_planning_agent"],
    "requires": ["process_framework_establishment", "domain_task_management"],
    "related": ["pattern_quality_assurance", "pattern_coordination_optimization"]
  },
  "context_templates": {
    "task_context": "When applying successful breakdown pattern: Establish framework first, provide complete context, minimize dependencies, integrate quality checkpoints.",
    "agent_context": "Successful breakdown requires {framework_establishment} with {context_completeness} and {dependency_optimization} approach."
  },
  "isolation_requirements": {
    "minimum_context": [
      "task_breakdown_methodologies",
      "framework_establishment_guide",
      "context_provision_strategies", 
      "quality_integration_procedures"
    ],
    "validation_criteria": [
      "Can identify when pattern applies",
      "Can execute pattern steps correctly",
      "Can adapt pattern to specific contexts",
      "Can measure pattern effectiveness"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "effectiveness_score": 0.95,
    "source": "pattern_extraction_from_successful_executions",
    "confidence_level": "high",
    "applicability_scope": "broad"
  }
}
```

### System Knowledge Entity
```json
{
  "id": "system_core_principles",
  "type": "system",
  "name": "Core System Principles",
  "version": "1.0.0",
  "domain": "system_architecture",
  "process_frameworks": ["system_operation", "self_improvement"],
  "content": {
    "summary": "Fundamental principles that guide all system operations and evolution",
    "core_concepts": [
      "Process-first, never task-first approach",
      "Entity-based systematic architecture",
      "Systematic learning through process accumulation",
      "Recursive process-driven decomposition"
    ],
    "procedures": [
      "Process framework establishment before execution",
      "Entity relationship management",
      "Systematic learning integration",
      "Self-improvement through optimization"
    ],
    "examples": [
      "Process discovery before task execution",
      "Entity framework enabling systematic composition",
      "Event-driven optimization and learning",
      "Rolling review triggering systematic improvement"
    ],
    "quality_criteria": [
      "Process frameworks established systematically",
      "Entity relationships maintained consistently",
      "Learning captured and applied effectively",
      "System improvement demonstrated measurably"
    ],
    "common_pitfalls": [
      "Attempting task execution without framework establishment",
      "Ignoring entity relationship requirements",
      "Failing to capture learning from executions",
      "Ad-hoc improvements without systematic analysis"
    ]
  },
  "relationships": {
    "enables": ["all_system_components"],
    "requires": ["none"],
    "related": ["system_architecture", "system_evolution_strategy"]
  },
  "context_templates": {
    "task_context": "All system operations must follow core principles: establish frameworks first, maintain entity relationships, capture learning, improve systematically.",
    "agent_context": "System operation requires adherence to {principle_type} with {framework_compliance} and {learning_integration}."
  },
  "isolation_requirements": {
    "minimum_context": [
      "core_principles_complete_specification",
      "framework_establishment_requirements", 
      "entity_relationship_management_guide",
      "systematic_learning_procedures"
    ],
    "validation_criteria": [
      "Understands and applies core principles",
      "Can establish frameworks before execution",
      "Can maintain entity relationships correctly",
      "Can integrate learning systematically"
    ]
  },
  "metadata": {
    "created_at": "2024-01-15T10:00:00Z", 
    "last_updated": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "effectiveness_score": 1.0,
    "source": "project_principles_conversion",
    "criticality": "fundamental",
    "change_impact": "system_wide"
  }
}
```

## Relationship Structure

### Relationship Types
```json
{
  "enables": ["knowledge_ids_that_this_knowledge_makes_possible"],
  "requires": ["prerequisite_knowledge_ids_needed_for_this_knowledge"],
  "related": ["associated_knowledge_ids_with_logical_connections"],
  "enhances": ["knowledge_ids_that_this_knowledge_improves"], 
  "specializes": ["knowledge_ids_that_this_knowledge_is_a_specialization_of"],
  "generalizes": ["knowledge_ids_that_this_knowledge_is_a_generalization_of"]
}
```

### Relationship Metadata
```json
{
  "relationship_type": "enables|requires|related|enhances|specializes|generalizes",
  "strength": "0.0-1.0 - strength of relationship",
  "context": "optional context about when relationship applies",
  "bidirectional": "boolean - whether relationship works both ways"
}
```

## Context Template Structure

### Template Types
```json
{
  "task_context": "Template for providing context when this knowledge applies to a task",
  "agent_context": "Template for agent specialization context",
  "process_context": "Template for process execution context", 
  "validation_context": "Template for validation and quality checking",
  "learning_context": "Template for learning and improvement activities"
}
```

### Template Variables
Templates can include variables for dynamic context assembly:
- `{domain_type}` - The primary domain
- `{framework_type}` - The process framework being used
- `{complexity_level}` - Task complexity assessment
- `{quality_requirements}` - Quality standards to meet
- `{isolation_level}` - Required isolation capabilities
- `{coordination_aspects}` - Coordination requirements

## Metadata Standards

### Required Metadata Fields
```json
{
  "created_at": "ISO 8601 timestamp",
  "last_updated": "ISO 8601 timestamp",
  "usage_count": "integer - number of times used",
  "effectiveness_score": "0.0-1.0 - measured effectiveness",
  "source": "documentation|task_execution|system_learning|manual_creation"
}
```

### Optional Metadata Fields
```json
{
  "tags": ["array of classification tags"],
  "priority": "low|medium|high|critical",
  "complexity_level": "simple|moderate|complex|expert",
  "automation_potential": "none|low|medium|high",
  "specialization_level": "general|intermediate|advanced|expert",
  "confidence_level": "low|medium|high|verified",
  "applicability_scope": "narrow|moderate|broad|universal",
  "change_frequency": "stable|evolving|dynamic|experimental"
}
```

## File Organization

### Directory Structure
```
knowledge/
├── domains/
│   ├── software_development.json
│   ├── system_architecture.json
│   └── task_management.json
├── processes/
│   ├── task_breakdown.json
│   ├── quality_evaluation.json
│   └── framework_establishment.json
├── agents/
│   ├── planning_agent.json
│   ├── agent_selector.json
│   └── task_evaluator.json
├── tools/
│   ├── entity_manager.json
│   ├── context_engine.json
│   └── quality_validator.json
├── patterns/
│   ├── successful_breakdown.json
│   ├── effective_coordination.json
│   └── quality_improvement.json
└── system/
    ├── core_principles.json
    ├── architecture_overview.json
    └── evolution_strategy.json
```

### Naming Conventions
- **File names**: `snake_case.json`
- **Entity IDs**: `{type}_{descriptive_name}` 
- **Relationship references**: Use full entity ID
- **Template variables**: `{variable_name}` format

This format enables simple file-based storage that can easily migrate to graph databases while providing all necessary structure for the MVP knowledge system.