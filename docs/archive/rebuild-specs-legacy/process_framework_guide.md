# Process Framework Guide

## Core Purpose

Processes are the system's mechanism for converting successful ad-hoc approaches into reusable, structured workflows. They represent the system's accumulated wisdom about how to solve specific types of problems efficiently and reliably, enabling automation and reducing unpredictability while preserving the flexibility for emergence and innovation.

## Fundamental Principles

### From Pattern to Process
The process framework captures successful patterns and transforms them into executable templates:
- **Pattern Recognition**: Optimizer Agent identifies recurring successful approaches
- **Template Extraction**: Successful workflows abstracted into parameterized templates
- **Automation Integration**: Manual steps converted to programmatic execution where possible
- **Evolution Through Usage**: Process effectiveness measured and templates refined over time

### Structured Flexibility
Processes provide structure without eliminating agent autonomy:
- **Clear Frameworks**: Processes define workflow structure and coordination points
- **Parameter Flexibility**: Templates accept parameters for customization
- **Agent Autonomy**: Agents maintain decision-making authority within process steps
- **Emergent Capabilities**: New approaches can develop within process frameworks

### Composition and Orchestration
Processes can be combined and nested for complex workflows:
- **Process Composition**: Processes can call other processes as steps
- **Parallel Execution**: Multiple process branches can execute simultaneously
- **Conditional Logic**: Processes can adapt based on conditions and outcomes
- **Error Handling**: Processes include recovery and fallback mechanisms

## Process Structure

### Process Template Schema
```json
{
  "name": "process_name",
  "version": "1.0.0",
  "description": "Human-readable description of what this process accomplishes",
  "category": "breakdown|context_addition|tool_creation|evaluation|optimization|custom",
  "parameters_schema": {
    "parameter_name": {
      "type": "string|number|boolean|object|array",
      "required": true|false,
      "default": "default_value",
      "description": "Parameter description"
    }
  },
  "template": [
    {
      "step_id": "unique_step_identifier",
      "step_type": "agent_prompt|tool_call|subtask_spawn|condition_check|loop|parallel_execution|wait_for_completion",
      "parameters": {
        "step_specific_parameters": "with_parameter_substitution_{{parameter_name}}"
      },
      "conditions": ["optional_condition_expressions"],
      "next_steps": ["list_of_next_step_ids"],
      "error_handler": "optional_error_handler_step_id"
    }
  ],
  "success_criteria": [
    "criterion_1",
    "criterion_2"
  ],
  "metadata": {
    "usage_count": 0,
    "success_rate": 0.0,
    "average_execution_time": 0,
    "created_by_task_id": null,
    "optimization_opportunities": []
  }
}
```

### Process Step Types

#### Agent Prompt Steps
Execute agent reasoning and decision-making within structured context
```json
{
  "step_id": "analyze_requirements",
  "step_type": "agent_prompt",
  "parameters": {
    "agent_type": "{{assigned_agent_type}}",
    "prompt_template": "Analyze the following requirements and identify key components: {{requirements_text}}",
    "expected_output_format": "structured_json",
    "context_documents": ["requirements_analysis_guide"],
    "additional_tools": ["requirement_parser"],
    "timeout_seconds": 300
  },
  "next_steps": ["validate_analysis"]
}
```

#### Tool Call Steps
Execute specific tools with parameter substitution
```json
{
  "step_id": "search_knowledge_base",
  "step_type": "tool_call",
  "parameters": {
    "tool_name": "search_documents",
    "tool_parameters": {
      "query": "{{search_query}}",
      "category": "{{document_category}}",
      "max_results": 5
    },
    "expected_output": "document_list"
  },
  "next_steps": ["process_search_results"]
}
```

#### Subtask Spawn Steps
Create coordinated subtasks within process workflow
```json
{
  "step_id": "create_implementation_subtasks",
  "step_type": "subtask_spawn",
  "parameters": {
    "subtasks": [
      {
        "name": "implement_{{component_name}}",
        "instruction": "Implement {{component_name}} component according to specifications: {{component_specs}}",
        "agent_type": "{{implementation_agent_type}}",
        "dependencies": [],
        "additional_context": ["{{component_name}}_specifications"],
        "priority": "{{component_priority}}"
      }
    ],
    "coordination_mode": "parallel|sequential|dependency_based"
  },
  "next_steps": ["wait_for_subtask_completion"]
}
```

#### Condition Check Steps
Evaluate conditions for process flow control
```json
{
  "step_id": "check_quality_threshold",
  "step_type": "condition_check",
  "parameters": {
    "condition_expression": "{{quality_score}} >= {{quality_threshold}}",
    "condition_type": "boolean_expression",
    "variables": {
      "quality_score": "{{previous_step.quality_evaluation.score}}",
      "quality_threshold": 0.8
    }
  },
  "next_steps": ["proceed_to_deployment"],
  "else_steps": ["quality_improvement_loop"]
}
```

#### Loop Steps
Implement iterative process execution
```json
{
  "step_id": "iterative_improvement",
  "step_type": "loop",
  "parameters": {
    "loop_condition": "{{improvement_score}} < {{target_score}} AND {{iteration_count}} < {{max_iterations}}",
    "loop_body": ["identify_improvements", "apply_improvements", "measure_improvement"],
    "loop_variables": {
      "iteration_count": 0,
      "max_iterations": 5,
      "target_score": 0.9
    }
  },
  "next_steps": ["finalize_improvements"]
}
```

#### Parallel Execution Steps
Coordinate concurrent process branches
```json
{
  "step_id": "parallel_analysis",
  "step_type": "parallel_execution",
  "parameters": {
    "branches": [
      {
        "branch_id": "technical_analysis",
        "steps": ["analyze_technical_requirements", "evaluate_technical_feasibility"]
      },
      {
        "branch_id": "business_analysis", 
        "steps": ["analyze_business_requirements", "evaluate_business_impact"]
      }
    ],
    "synchronization": "wait_for_all|wait_for_any|wait_for_majority"
  },
  "next_steps": ["synthesize_analysis_results"]
}
```

#### Wait for Completion Steps
Coordinate dependencies and timing
```json
{
  "step_id": "wait_for_dependencies",
  "step_type": "wait_for_completion",
  "parameters": {
    "wait_for": ["subtask_id_1", "subtask_id_2", "external_dependency"],
    "timeout_seconds": 3600,
    "timeout_action": "proceed_with_available_results|fail_process|trigger_escalation"
  },
  "next_steps": ["process_completed_dependencies"]
}
```

### Parameter Substitution

#### Template Variable Syntax
- **Simple Variables**: `{{variable_name}}`
- **Nested Variables**: `{{object.property.subproperty}}`
- **Array Access**: `{{array_name[index]}}`
- **Conditional Variables**: `{{variable_name || default_value}}`
- **Computed Variables**: `{{variable_1 + variable_2}}`

#### Parameter Sources
- **Process Parameters**: Values passed when process is executed
- **Step Outputs**: Results from previous process steps
- **Entity Attributes**: Properties of related entities
- **System State**: Current system configuration and status
- **Context Variables**: Dynamic values based on execution context

#### Parameter Validation
```json
{
  "parameters_schema": {
    "task_complexity": {
      "type": "string",
      "enum": ["simple", "moderate", "complex"],
      "required": true,
      "description": "Complexity level of the task being processed"
    },
    "agent_specializations": {
      "type": "array",
      "items": {"type": "string"},
      "required": false,
      "default": ["general"],
      "description": "List of required agent specializations"
    },
    "quality_threshold": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.8,
      "description": "Minimum quality score for process success"
    }
  }
}
```

## Process Categories

### Task Breakdown Processes
Convert complex tasks into manageable subtask structures
```json
{
  "standard_task_breakdown": {
    "description": "Standard process for decomposing complex tasks",
    "template": [
      {"step_id": "analyze_complexity", "step_type": "agent_prompt"},
      {"step_id": "identify_components", "step_type": "agent_prompt"},
      {"step_id": "design_subtask_structure", "step_type": "agent_prompt"},
      {"step_id": "create_subtasks", "step_type": "subtask_spawn"},
      {"step_id": "validate_breakdown", "step_type": "agent_prompt"}
    ]
  },
  "domain_specific_breakdown": {
    "description": "Breakdown process specialized for specific domains",
    "template": [
      {"step_id": "load_domain_context", "step_type": "tool_call"},
      {"step_id": "apply_domain_patterns", "step_type": "agent_prompt"},
      {"step_id": "create_domain_subtasks", "step_type": "subtask_spawn"}
    ]
  }
}
```

### Context Addition Processes
Systematically identify and provide relevant context
```json
{
  "context_discovery": {
    "description": "Comprehensive process for identifying needed context",
    "template": [
      {"step_id": "analyze_knowledge_gaps", "step_type": "agent_prompt"},
      {"step_id": "search_existing_knowledge", "step_type": "tool_call"},
      {"step_id": "identify_external_sources", "step_type": "agent_prompt"},
      {"step_id": "gather_additional_context", "step_type": "tool_call"},
      {"step_id": "validate_context_relevance", "step_type": "agent_prompt"}
    ]
  }
}
```

### Tool Creation Processes
Systematically create and integrate new capabilities
```json
{
  "capability_development": {
    "description": "Process for developing new system capabilities",
    "template": [
      {"step_id": "analyze_capability_gap", "step_type": "agent_prompt"},
      {"step_id": "search_existing_tools", "step_type": "tool_call"},
      {"step_id": "design_tool_specification", "step_type": "agent_prompt"},
      {"step_id": "implement_tool", "step_type": "agent_prompt"},
      {"step_id": "test_tool_integration", "step_type": "tool_call"},
      {"step_id": "validate_tool_effectiveness", "step_type": "agent_prompt"}
    ]
  }
}
```

### Quality Evaluation Processes
Comprehensive assessment of task completion
```json
{
  "multi_dimensional_evaluation": {
    "description": "Comprehensive quality evaluation across multiple dimensions",
    "template": [
      {"step_id": "evaluate_functional_quality", "step_type": "agent_prompt"},
      {"step_id": "evaluate_completeness", "step_type": "agent_prompt"},
      {"step_id": "evaluate_craft_quality", "step_type": "agent_prompt"},
      {"step_id": "run_automated_tests", "step_type": "tool_call"},
      {"step_id": "synthesize_evaluation", "step_type": "agent_prompt"},
      {"step_id": "generate_improvement_recommendations", "step_type": "agent_prompt"}
    ]
  }
}
```

### Optimization Processes
Systematic improvement of system components
```json
{
  "entity_optimization": {
    "description": "Process for optimizing entity performance and effectiveness",
    "template": [
      {"step_id": "analyze_usage_patterns", "step_type": "tool_call"},
      {"step_id": "identify_optimization_opportunities", "step_type": "agent_prompt"},
      {"step_id": "design_improvements", "step_type": "agent_prompt"},
      {"step_id": "implement_improvements", "step_type": "agent_prompt"},
      {"step_id": "test_improvements", "step_type": "tool_call"},
      {"step_id": "measure_improvement_impact", "step_type": "agent_prompt"}
    ]
  }
}
```

## Process Execution Engine

### Execution Context
```python
class ProcessExecutionContext:
    def __init__(self, process_id: int, parameters: Dict[str, Any], 
                 initiating_task_id: int):
        self.process_id = process_id
        self.parameters = parameters
        self.initiating_task_id = initiating_task_id
        self.execution_id = generate_unique_id()
        self.step_results = {}
        self.execution_start_time = time.time()
        self.current_step = None
        self.execution_status = "running"
        
    def get_variable(self, variable_path: str) -> Any:
        """Resolve variable from parameters, step results, or context"""
        pass
        
    def set_step_result(self, step_id: str, result: Any):
        """Store result from completed step"""
        pass
```

### Step Execution Framework
```python
class ProcessStepExecutor:
    async def execute_step(self, step: ProcessStep, context: ProcessExecutionContext) -> Any:
        """Execute individual process step"""
        try:
            # Substitute parameters in step configuration
            resolved_step = self.substitute_parameters(step, context)
            
            # Execute step based on type
            if step.step_type == "agent_prompt":
                result = await self.execute_agent_prompt(resolved_step, context)
            elif step.step_type == "tool_call":
                result = await self.execute_tool_call(resolved_step, context)
            elif step.step_type == "subtask_spawn":
                result = await self.execute_subtask_spawn(resolved_step, context)
            # ... other step types
            
            # Store result and log event
            context.set_step_result(step.step_id, result)
            await self.log_step_completion(step, result, context)
            
            return result
            
        except Exception as e:
            # Handle error according to step configuration
            if step.error_handler:
                return await self.execute_error_handler(step.error_handler, e, context)
            else:
                raise ProcessExecutionError(f"Step {step.step_id} failed: {e}")
```

### Process Orchestration
```python
class ProcessOrchestrator:
    async def execute_process(self, process_id: int, parameters: Dict[str, Any], 
                            initiating_task_id: int) -> Dict[str, Any]:
        """Execute complete process template"""
        # Create execution context
        context = ProcessExecutionContext(process_id, parameters, initiating_task_id)
        
        # Load process template
        process = await self.entity_manager.get_entity(process_id, EntityType.PROCESS)
        
        # Validate parameters
        await self.validate_parameters(process, parameters)
        
        # Execute process steps
        try:
            result = await self.execute_step_sequence(process.template, context)
            context.execution_status = "completed"
            return result
            
        except Exception as e:
            context.execution_status = "failed"
            await self.log_process_failure(process, context, e)
            raise
            
        finally:
            # Update process metrics
            await self.update_process_metrics(process, context)
```

## Process Discovery and Evolution

### Pattern Recognition
```python
class ProcessPatternDiscovery:
    async def analyze_task_patterns(self, time_window_days: int = 30) -> List[ProcessPattern]:
        """Analyze recent task executions for common patterns"""
        # Query successful task executions
        successful_tasks = await self.get_successful_tasks(time_window_days)
        
        # Extract execution patterns
        patterns = []
        for task_group in self.group_similar_tasks(successful_tasks):
            pattern = await self.extract_execution_pattern(task_group)
            if self.is_pattern_significant(pattern):
                patterns.append(pattern)
                
        return patterns
        
    def is_pattern_significant(self, pattern: ProcessPattern) -> bool:
        """Determine if pattern is worth converting to process"""
        return (pattern.frequency >= 5 and 
                pattern.success_rate >= 0.8 and
                pattern.average_efficiency_gain >= 0.2)
```

### Process Template Generation
```python
class ProcessTemplateGenerator:
    async def create_process_from_pattern(self, pattern: ProcessPattern) -> Process:
        """Convert successful pattern into reusable process template"""
        # Analyze pattern steps and extract template
        template_steps = []
        for step in pattern.common_steps:
            template_step = await self.generalize_step(step, pattern.variations)
            template_steps.append(template_step)
            
        # Define parameter schema from pattern variations
        parameters_schema = self.extract_parameter_schema(pattern.variations)
        
        # Create process entity
        process = Process(
            name=f"generated_{pattern.category}_{pattern.identifier}",
            description=f"Auto-generated process from pattern: {pattern.description}",
            category=pattern.category,
            template=template_steps,
            parameters_schema=parameters_schema,
            success_criteria=pattern.success_criteria
        )
        
        return process
```

### Process Optimization
```python
class ProcessOptimizer:
    async def optimize_process(self, process_id: int) -> Process:
        """Optimize existing process based on usage data"""
        # Analyze process execution history
        executions = await self.get_process_executions(process_id)
        performance_data = await self.analyze_performance(executions)
        
        # Identify optimization opportunities
        optimizations = []
        if performance_data.has_bottleneck_steps():
            optimizations.extend(await self.optimize_bottleneck_steps(performance_data))
        if performance_data.has_redundant_steps():
            optimizations.extend(await self.remove_redundant_steps(performance_data))
        if performance_data.has_parallel_opportunities():
            optimizations.extend(await self.parallelize_steps(performance_data))
            
        # Apply optimizations and create new version
        optimized_process = await self.apply_optimizations(process_id, optimizations)
        
        return optimized_process
```

## Process Quality and Governance

### Process Validation
```python
class ProcessValidator:
    def validate_process_template(self, process: Process) -> ValidationResult:
        """Validate process template structure and logic"""
        errors = []
        warnings = []
        
        # Validate step references
        step_ids = {step.step_id for step in process.template}
        for step in process.template:
            for next_step in step.next_steps:
                if next_step not in step_ids:
                    errors.append(f"Step {step.step_id} references undefined step {next_step}")
                    
        # Validate parameter usage
        used_parameters = self.extract_used_parameters(process.template)
        defined_parameters = set(process.parameters_schema.keys())
        for param in used_parameters:
            if param not in defined_parameters:
                warnings.append(f"Parameter {param} used but not defined in schema")
                
        # Validate circular dependencies
        if self.has_circular_dependencies(process.template):
            errors.append("Process template contains circular step dependencies")
            
        return ValidationResult(errors=errors, warnings=warnings)
```

### Process Testing
```python
class ProcessTester:
    async def test_process(self, process_id: int, test_parameters: List[Dict[str, Any]]) -> TestResults:
        """Test process with various parameter combinations"""
        results = []
        for params in test_parameters:
            try:
                result = await self.execute_process_test(process_id, params)
                results.append(TestResult(
                    parameters=params,
                    success=True,
                    execution_time=result.execution_time,
                    output=result.output
                ))
            except Exception as e:
                results.append(TestResult(
                    parameters=params,
                    success=False,
                    error=str(e)
                ))
                
        return TestResults(results=results)
```

### Process Metrics and Analytics
```python
class ProcessAnalytics:
    async def generate_process_metrics(self, process_id: int) -> ProcessMetrics:
        """Generate comprehensive metrics for process performance"""
        executions = await self.get_process_executions(process_id, days=30)
        
        return ProcessMetrics(
            total_executions=len(executions),
            success_rate=sum(1 for e in executions if e.success) / len(executions),
            average_execution_time=statistics.mean(e.execution_time for e in executions),
            parameter_usage_patterns=self.analyze_parameter_patterns(executions),
            step_performance=self.analyze_step_performance(executions),
            optimization_opportunities=await self.identify_optimization_opportunities(executions)
        )
```

## Process Integration Patterns

### Agent-Process Integration
Agents trigger processes and interact with process execution:
```python
# Agent tool for process execution
@mcp_tool
async def execute_process(self, process_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a named process with parameters"""
    process = await self.find_process_by_name(process_name)
    if not process:
        raise ToolExecutionError(f"Process {process_name} not found")
        
    result = await self.process_engine.execute_process(
        process.id, 
        parameters, 
        self.current_task_id
    )
    
    return result
```

### Task-Process Integration
Tasks can be created and managed through process templates:
```python
# Process step for coordinated task creation
{
  "step_id": "create_implementation_tasks",
  "step_type": "subtask_spawn",
  "parameters": {
    "subtasks": [
      {
        "name": "implement_{{component}}",
        "instruction": "Implement {{component}} following {{specifications}}",
        "agent_type": "{{agent_specialization}}",
        "process_template": "component_implementation_process",
        "process_parameters": {
          "component_name": "{{component}}",
          "specifications": "{{specifications}}"
        }
      }
    ]
  }
}
```

### Event-Process Integration
Processes generate events for tracking and optimization:
```python
# Automatic event generation during process execution
await self.event_logger.log_event(
    EventType.PROCESS_EXECUTED,
    EntityType.PROCESS,
    process_id,
    related_entities={
        "task": [initiating_task_id],
        "agent": [executing_agent_id]
    },
    event_data={
        "parameters": parameters,
        "execution_time": execution_time,
        "steps_completed": len(completed_steps),
        "success": execution_success
    }
)
```

## Success Metrics

Process framework success measured through:

### Automation Metrics
- **Process Coverage**: Percentage of task types with available process templates
- **Process Usage**: Frequency of process execution vs. manual task handling
- **Automation Effectiveness**: Reduction in agent reasoning time through process automation

### Quality Metrics  
- **Process Success Rate**: Percentage of process executions that complete successfully
- **Process Efficiency**: Time and resource savings compared to manual approaches
- **Process Reliability**: Consistency of outcomes across process executions

### Evolution Metrics
- **Pattern Discovery Rate**: Speed of converting successful patterns to processes
- **Process Optimization Frequency**: Rate of process improvement through usage data
- **Process Ecosystem Growth**: Expansion of process library and capabilities

The process framework transforms the agent system from reactive problem-solving to proactive workflow automation, enabling systematic improvement and predictable outcomes while preserving the flexibility for innovation and emergence.