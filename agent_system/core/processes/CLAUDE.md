# CLAUDE.md - Process Framework

## Module Overview

The processes module implements The System's core process-first architecture, providing the framework for systematic domain analysis and task execution. It contains base process classes, the neutral task process for execution, specialized tool processes, and the process registry for framework management. All processes ensure systematic structure establishment before execution.

## Key Components

- **base.py**: Abstract base classes for process implementation and execution patterns
- **neutral_task_process.py**: Core process for systematic task execution with framework validation
- **registry.py**: Process registration and discovery system for framework selection
- **system_initialization_process.py**: Bootstrap process for system establishment
- **tool_processes/**: Specialized processes for each core MCP tool operation

## Common Tasks

### Creating New Process Framework
1. Create process class inheriting from `BaseProcess` in `base.py`
2. Implement required methods: `analyze_domain()`, `establish_framework()`, `execute_with_framework()`
3. Register process in `registry.py` with domain patterns
4. Add process validation and completeness scoring
5. Test framework establishment and execution patterns

### Adding Tool Process
1. Create tool-specific process in `tool_processes/` directory
2. Implement tool execution within process boundaries
3. Add framework validation for tool requirements
4. Register with tool registry and MCP integration
5. Test tool process with agent runtime

### Updating Process Registry
1. Modify process registration in `registry.py`
2. Add domain matching patterns and criteria
3. Update process selection algorithms
4. Test process discovery and framework matching
5. Document process capabilities and patterns

### Implementing Domain Analysis
1. Add domain-specific analysis patterns to process
2. Implement complexity assessment and decomposition rules
3. Create framework completeness validation
4. Add success criteria generation logic
5. Test with various domain scenarios

## Architecture & Patterns

- **Process-First Design**: Framework establishment mandatory before execution
- **Domain Analysis**: Systematic assessment of task complexity and requirements
- **Framework Validation**: Completeness scoring and gap detection
- **Isolated Success**: Every subtask designed for independent completion
- **Registry Pattern**: Dynamic process discovery based on domain characteristics
- **Event Integration**: Comprehensive tracking for process optimization

## Process Types

### Core Processes
- **NeutralTaskProcess**: Universal task execution with framework establishment
- **SystemInitializationProcess**: Bootstrap process for system setup
- **DomainAnalysisProcess**: Specialized framework analysis and establishment

### Tool Processes (6 Core Tools)
- **BreakDownTaskProcess**: Recursive task decomposition with framework validation
- **CreateSubtaskProcess**: Agent spawning and task creation within boundaries
- **NeedMoreContextProcess**: Knowledge gap resolution and context expansion
- **NeedMoreToolsProcess**: Dynamic capability discovery and tool requests
- **EndTaskProcess**: Task completion with result validation
- **FlagForReviewProcess**: Human oversight escalation with context preservation

## Testing

### Process Framework Testing
```python
# Test framework establishment
process = CustomProcess()
framework = await process.establish_framework({
    "domain": "test_domain",
    "complexity": 5,
    "requirements": ["req1", "req2"]
})
assert framework.completeness_score > 0.8
```

### Process Execution Testing
```python
# Test process execution with framework
result = await process.execute_with_framework(
    task_data=task_data,
    framework=established_framework
)
assert result.status == "success"
assert len(result.subtasks_created) > 0
```

### Registry Testing
```python
# Test process discovery
registry = ProcessRegistry()
process_class = registry.find_best_process({
    "domain": "data_processing",
    "complexity": 3
})
assert process_class is not None
```

## Performance Considerations

- **Framework Caching**: Established frameworks cached for similar tasks
- **Domain Pattern Matching**: Efficient algorithms for process selection
- **Async Execution**: All process operations use async patterns
- **Event Batching**: Process events batched for high-throughput scenarios
- **Memory Management**: Proper cleanup of process state and temporary data

## Gotchas & Tips

### Process Development
- Always inherit from `BaseProcess` for proper integration
- Implement all required abstract methods completely
- Use framework validation before any execution attempts
- Design for isolated subtask success with complete context
- Add comprehensive error handling and rollback logic

### Framework Design
- Establish systematic structure before decomposition
- Validate framework completeness with scoring
- Ensure isolated success capability for all subtasks
- Use knowledge system for complete context assembly
- Document framework patterns for reuse

### Domain Analysis
- Assess complexity and decomposition requirements
- Identify dependencies and execution constraints
- Create success criteria and validation patterns
- Use existing domain knowledge and patterns
- Generate learnings for future framework improvement

### Registry Integration
- Register processes with clear domain patterns
- Implement proper matching algorithms
- Test process selection with various scenarios
- Update registry as new processes are added
- Document process capabilities and limitations

### Tool Process Implementation
- Validate tool availability and permissions
- Ensure tool execution within process boundaries
- Handle tool failures with proper error recovery
- Integrate with MCP protocol correctly
- Test tool processes with actual agent runtime

## Integration Points

- **Universal Agent Runtime**: Processes executed within runtime boundaries
- **Entity Manager**: Process state persisted through entity management
- **Knowledge System**: Context assembly and gap detection integration
- **Tool System**: Tool processes integrate with MCP protocol
- **Event System**: Process execution tracked for optimization

## Common Patterns

### Process Implementation Pattern
```python
class CustomProcess(BaseProcess):
    async def analyze_domain(self, domain_data: Dict[str, Any]) -> DomainAnalysis:
        # Assess domain complexity and requirements
        # Identify decomposition patterns
        # Return analysis with framework needs
        
    async def establish_framework(self, analysis: DomainAnalysis) -> ProcessFramework:
        # Create systematic structure
        # Validate completeness
        # Return established framework
        
    async def execute_with_framework(
        self, 
        task_data: Dict[str, Any], 
        framework: ProcessFramework
    ) -> ProcessResult:
        # Execute within framework boundaries
        # Create isolated subtasks
        # Return execution results
```

### Tool Process Pattern
```python
class ToolSpecificProcess(BaseProcess):
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"{tool_name}_process")
    
    async def execute_tool_with_framework(
        self, 
        parameters: Dict[str, Any],
        framework: ProcessFramework
    ) -> ProcessResult:
        # Validate tool availability
        # Execute within framework boundaries
        # Handle results and errors
```

### Registry Registration Pattern
```python
# In registry.py
def register_process(process_class: Type[BaseProcess], patterns: List[str]):
    """Register process with domain matching patterns."""
    registry[process_class.__name__] = {
        "class": process_class,
        "patterns": patterns,
        "complexity_range": (min_complexity, max_complexity)
    }
```

### Framework Validation Pattern
```python
def validate_framework_completeness(framework: ProcessFramework) -> float:
    """Score framework completeness from 0.0 to 1.0."""
    score = 0.0
    
    # Check required components
    if framework.has_decomposition_rules:
        score += 0.3
    if framework.has_success_criteria:
        score += 0.3
    if framework.has_context_requirements:
        score += 0.2
    if framework.has_validation_patterns:
        score += 0.2
        
    return score
```