# Process-First Architecture Specification

## Process-First Implementation Strategy

### Systematic Framework + Strategic LLM Architecture
Processes are systematic Python frameworks that:
- Establish comprehensive domain structure before any task execution
- Handle systematic analysis, framework validation, and domain coordination
- Make strategic LLM calls only when systematic reasoning within established frameworks is needed
- Execute systematic functions for comprehensive entity operations
- Include systematic error handling and framework rollback capabilities

### Process-First Categories

#### 1. Process Discovery Process (Primary Framework)
**The Systematic Domain Analysis Process - Applied to ALL tasks before execution**

```python
# process_discovery_process.py - The systematic framework establishment process applied to every task
class ProcessDiscoveryProcess:
    """Systematic process applied to every task for comprehensive framework establishment before execution"""
    
    async def execute(self, task_id: int):
        task = await self.sys.get_task(task_id)
        
        # PHASE 1: COMPREHENSIVE DOMAIN ANALYSIS (ALWAYS FIRST)
        domain_analysis_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Analyze domain structure requirements for: {task.instruction}",
            agent_type="process_discovery",
            context=["process_discovery_guide", "domain_analysis_patterns"],
            process="domain_analysis_process"
        )
        
        await self.sys.wait_for_tasks([domain_analysis_task_id])
        domain_analysis = await self.sys.get_task_result(domain_analysis_task_id)
        
        # PHASE 2: SYSTEMATIC PROCESS FRAMEWORK IDENTIFICATION
        process_gap_analysis_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Identify missing systematic processes for domain: {domain_analysis.domain_type}",
            agent_type="process_discovery",
            context=["process_framework_library", "systematic_process_patterns"],
            parameters={
                "domain_analysis": domain_analysis,
                "required_systematic_structure": domain_analysis.framework_requirements,
                "existing_processes": await self.sys.get_applicable_processes(domain_analysis.domain_type)
            }
        )
        
        await self.sys.wait_for_tasks([process_gap_analysis_task_id])
        process_gaps = await self.sys.get_task_result(process_gap_analysis_task_id)
        
        # PHASE 3: SYSTEMATIC FRAMEWORK ESTABLISHMENT (BEFORE ANY EXECUTION)
        if process_gaps.missing_critical_processes:
            framework_creation_tasks = []
            
            for missing_process in process_gaps.missing_critical_processes:
                creation_task_id = await self.sys.create_subtask(
                    parent_id=task_id,
                    instruction=f"Establish systematic process framework: {missing_process.name}",
                    agent_type="process_discovery",
                    context=["process_creation_guide", "systematic_framework_patterns"],
                    parameters={
                        "process_specification": missing_process,
                        "domain_context": domain_analysis,
                        "isolation_requirements": missing_process.isolated_task_success_requirements
                    }
                )
                framework_creation_tasks.append(creation_task_id)
            
            # Wait for ALL systematic frameworks to be established
            await self.sys.wait_for_tasks(framework_creation_tasks)
        
        # PHASE 4: SYSTEMATIC FRAMEWORK VALIDATION
        framework_validation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Validate systematic framework completeness for isolated task success",
            agent_type="process_discovery",
            context=["framework_validation_guide"],
            parameters={
                "established_frameworks": await self.sys.get_domain_processes(domain_analysis.domain_type),
                "isolation_requirements": domain_analysis.isolated_task_requirements,
                "domain_completeness_criteria": domain_analysis.systematic_completeness_requirements
            }
        )
        
        await self.sys.wait_for_tasks([framework_validation_task_id])
        validation_result = await self.sys.get_task_result(framework_validation_task_id)
        
        if not validation_result.framework_complete:
            # Framework incomplete - establish additional systematic structure
            await self.establish_additional_framework(task_id, validation_result.completeness_gaps)
        
        # PHASE 5: SYSTEMATIC TASK PREPARATION (ONLY AFTER COMPLETE FRAMEWORK)
        await self.sys.update_task(task_id, 
            process=validation_result.primary_systematic_process,
            additional_context=validation_result.systematic_framework_documentation,
            systematic_framework_id=validation_result.framework_id
        )
        
        # Now task can proceed to systematic neutral_task_process with complete framework
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_SYSTEMATIC_EXECUTION)
        
        return {
            "systematic_framework_established": True,
            "domain_type": domain_analysis.domain_type,
            "framework_id": validation_result.framework_id,
            "isolated_task_success_enabled": validation_result.isolation_capability
        }
```

#### 2. Systematic Neutral Task Process (Framework-Driven)
**The Systematic Task Process - Applied after framework establishment**

```python
# systematic_neutral_task_process.py - Applied only after systematic framework establishment
class SystematicNeutralTaskProcess:
    """Systematic task process applied only after comprehensive framework establishment"""
    
    async def execute(self, task_id: int):
        task = await self.sys.get_task(task_id)
        
        # Verify systematic framework exists (should always be true by this point)
        if not task.systematic_framework_id:
            raise SystematicFrameworkError("Task reached systematic execution without framework establishment")
        
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        # PHASE 1: SYSTEMATIC AGENT SELECTION (FRAMEWORK-DRIVEN)
        if not task.assigned_agent:
            agent_selection_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Select optimal agent for systematic framework: {systematic_framework.domain_type}",
                agent_type="agent_selector",
                context=["agent_capabilities_reference", "systematic_framework_guide"],
                parameters={
                    "systematic_framework": systematic_framework,
                    "framework_requirements": systematic_framework.agent_requirements,
                    "isolation_context": systematic_framework.isolated_execution_requirements
                }
            )
            
            await self.sys.wait_for_tasks([agent_selection_task_id])
            selected_agent = await self.sys.get_task_result(agent_selection_task_id)
            await self.sys.update_task(task_id, assigned_agent=selected_agent.agent_type)
        
        # PHASE 2: SYSTEMATIC CONTEXT ASSIGNMENT (FRAMEWORK-DEFINED)
        required_context = systematic_framework.determine_required_context(task.instruction)
        if required_context and not self.has_sufficient_context(task, required_context):
            context_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Provide systematic context for framework: {systematic_framework.domain_type}",
                agent_type="context_addition",
                context=["context_addition_guide", "systematic_framework_context_guide"],
                parameters={
                    "systematic_framework": systematic_framework,
                    "required_context": required_context,
                    "isolation_requirements": systematic_framework.context_isolation_requirements
                }
            )
            
            await self.sys.wait_for_tasks([context_task_id])
            context_result = await self.sys.get_task_result(context_task_id)
            await self.sys.add_context_to_task(task_id, context_result.systematic_context_documents)
        
        # PHASE 3: SYSTEMATIC TOOL ASSIGNMENT (FRAMEWORK-DEFINED)
        required_tools = systematic_framework.determine_required_tools(task.instruction, task.assigned_agent)
        if required_tools and not self.has_sufficient_tools(task, required_tools):
            tool_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Provide systematic tools for framework: {systematic_framework.domain_type}",
                agent_type="tool_addition",
                context=["tool_addition_guide", "systematic_framework_tool_guide"],
                parameters={
                    "systematic_framework": systematic_framework,
                    "required_tools": required_tools,
                    "framework_boundaries": systematic_framework.tool_usage_boundaries
                }
            )
            
            await self.sys.wait_for_tasks([tool_task_id])
            tool_result = await self.sys.get_task_result(tool_task_id)
            await self.sys.add_tools_to_task(task_id, tool_result.systematic_tools)
        
        # PHASE 4: ISOLATED TASK SUCCESS VALIDATION
        isolation_validation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Validate isolated task success capability within systematic framework",
            agent_type="process_discovery",
            context=["isolation_validation_guide"],
            parameters={
                "task_configuration": task,
                "systematic_framework": systematic_framework,
                "isolation_requirements": systematic_framework.isolated_success_criteria
            }
        )
        
        await self.sys.wait_for_tasks([isolation_validation_task_id])
        isolation_validation = await self.sys.get_task_result(isolation_validation_task_id)
        
        if not isolation_validation.can_succeed_in_isolation:
            # Add additional systematic context/tools for isolation capability
            await self.enhance_isolation_capability(task_id, isolation_validation.isolation_gaps)
        
        # PHASE 5: SYSTEMATIC EXECUTION READINESS
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
        return {
            "systematic_execution_ready": True,
            "framework_compliance": True,
            "isolation_capability_validated": True
        }
```

#### 3. Systematic Tool Processes (Framework-Compliant)
**Triggered by Agent Tool Calls Within Established Frameworks**

```python
# systematic_break_down_task_process.py - Framework-compliant task breakdown
class SystematicBreakDownTaskProcess:
    """Handles systematic task breakdown within established process frameworks"""
    
    async def execute(self, parent_task_id: int, breakdown_request: str, **tool_args):
        parent_task = await self.sys.get_task(parent_task_id)
        systematic_framework = await self.sys.get_systematic_framework(parent_task.systematic_framework_id)
        
        # PHASE 1: SYSTEMATIC BREAKDOWN PLANNING (FRAMEWORK-DRIVEN)
        planning_task_id = await self.sys.create_subtask(
            parent_id=parent_task_id,
            instruction=f"Plan systematic breakdown within framework: {systematic_framework.domain_type}",
            agent_type="planning_agent",
            context=["planning_agent_guide", "systematic_breakdown_patterns"],
            parameters={
                "parent_task": parent_task.instruction,
                "systematic_framework": systematic_framework,
                "breakdown_approach": breakdown_request,
                "framework_boundaries": systematic_framework.breakdown_boundaries,
                "isolation_requirements": systematic_framework.subtask_isolation_requirements
            }
        )
        
        await self.sys.wait_for_tasks([planning_task_id])
        breakdown_plan = await self.sys.get_task_result(planning_task_id)
        
        # PHASE 2: SYSTEMATIC FRAMEWORK VALIDATION FOR SUBTASKS
        framework_validation_task_id = await self.sys.create_subtask(
            parent_id=parent_task_id,
            instruction=f"Validate systematic framework adequacy for planned subtasks",
            agent_type="process_discovery",
            context=["framework_validation_guide"],
            parameters={
                "breakdown_plan": breakdown_plan,
                "systematic_framework": systematic_framework,
                "subtask_isolation_requirements": breakdown_plan.isolation_needs
            }
        )
        
        await self.sys.wait_for_tasks([framework_validation_task_id])
        framework_validation = await self.sys.get_task_result(framework_validation_task_id)
        
        if framework_validation.additional_frameworks_needed:
            # Establish additional systematic frameworks for subtasks
            for additional_framework in framework_validation.additional_frameworks_needed:
                await self.establish_systematic_framework(additional_framework)
        
        # PHASE 3: SYSTEMATIC SUBTASK CREATION (FRAMEWORK-COMPLIANT)
        subtask_ids = []
        for subtask_spec in breakdown_plan.subtasks:
            # Each subtask inherits or gets assigned appropriate systematic framework
            subtask_framework = self.determine_subtask_framework(subtask_spec, systematic_framework)
            
            subtask_id = await self.sys.create_subtask(
                parent_id=parent_task_id,
                instruction=subtask_spec.instruction,
                dependencies=subtask_spec.dependencies,
                priority=subtask_spec.priority,
                systematic_framework_id=subtask_framework.id,
                process=subtask_framework.primary_process or "systematic_neutral_task"
            )
            subtask_ids.append(subtask_id)
        
        # PHASE 4: SYSTEMATIC DEPENDENCY VALIDATION
        dependency_validation = await self.validate_systematic_dependencies(subtask_ids, systematic_framework)
        if not dependency_validation.dependencies_valid:
            await self.fix_systematic_dependencies(subtask_ids, dependency_validation.dependency_issues)
        
        await self.sys.update_task_state(parent_task_id, TaskState.WAITING_ON_DEPENDENCIES)
        await self.sys.add_task_dependencies(parent_task_id, subtask_ids)
        
        summary = f"Systematic breakdown complete: {len(subtask_ids)} framework-compliant subtasks created"
        return {
            "status": "systematic_breakdown_complete",
            "subtasks_created": subtask_ids,
            "systematic_framework_compliance": True,
            "isolation_capability_validated": True,
            "summary": summary
        }

# systematic_end_task_process.py - Framework-compliant task completion
class SystematicEndTaskProcess:
    """Handles systematic task completion within established frameworks"""
    
    async def execute(self, task_id: int, result: str, agent_assessment: str = ""):
        task = await self.sys.get_task(task_id)
        systematic_framework = await self.sys.get_systematic_framework(task.systematic_framework_id)
        
        # PHASE 1: SYSTEMATIC FRAMEWORK COMPLIANCE VALIDATION
        compliance_validation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Validate systematic framework compliance for task completion",
            agent_type="process_discovery",
            context=["framework_compliance_guide"],
            parameters={
                "task_result": result,
                "systematic_framework": systematic_framework,
                "framework_compliance_criteria": systematic_framework.completion_criteria,
                "isolation_success_validation": systematic_framework.isolation_validation_requirements
            }
        )
        
        # PHASE 2: SYSTEMATIC QUALITY EVALUATION (FRAMEWORK-AWARE)
        evaluation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Evaluate systematic completion quality within framework: {systematic_framework.domain_type}",
            agent_type="task_evaluator",
            context=["task_evaluator_guide", "systematic_framework_evaluation_guide"],
            parameters={
                "task_result": result,
                "agent_assessment": agent_assessment,
                "original_task": task.instruction,
                "systematic_framework": systematic_framework,
                "framework_quality_criteria": systematic_framework.quality_standards
            }
        )
        
        # PHASE 3: SYSTEMATIC SUMMARY CREATION (FRAMEWORK-CONTEXTUALIZED)
        summary_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Create systematic summary within framework context: {systematic_framework.domain_type}",
            agent_type="summary_agent",
            context=["summary_agent_guide", "systematic_framework_summary_guide"],
            parameters={
                "task_result": result,
                "task_context": task.instruction,
                "systematic_framework": systematic_framework,
                "framework_summary_requirements": systematic_framework.summary_standards
            }
        )
        
        # Wait for systematic validation and assessment
        await self.sys.wait_for_tasks([compliance_validation_task_id, evaluation_task_id, summary_task_id])
        
        compliance_result = await self.sys.get_task_result(compliance_validation_task_id)
        evaluation_result = await self.sys.get_task_result(evaluation_task_id)
        summary_result = await self.sys.get_task_result(summary_task_id)
        
        # PHASE 4: SYSTEMATIC COMPLETION DETERMINATION
        if (compliance_result.framework_compliant and 
            evaluation_result.quality_acceptable and 
            compliance_result.isolation_success_validated):
            
            await self.sys.update_task_state(task_id, TaskState.COMPLETED)
            await self.sys.set_task_result(task_id, {
                "result": result,
                "summary": summary_result.content,
                "evaluation": evaluation_result,
                "systematic_framework_compliance": compliance_result,
                "isolation_success_confirmed": True
            })
            
            # PHASE 5: SYSTEMATIC FRAMEWORK ENHANCEMENT
            if evaluation_result.suggests_framework_enhancement:
                framework_enhancement_task_id = await self.sys.create_subtask(
                    parent_id=task_id,
                    instruction=f"Enhance systematic framework based on successful execution",
                    agent_type="process_discovery",
                    context=["framework_enhancement_guide"],
                    parameters={
                        "successful_execution": result,
                        "systematic_framework": systematic_framework,
                        "enhancement_opportunities": evaluation_result.framework_enhancement_suggestions
                    }
                )
        else:
            # Systematic framework compliance or quality issues
            await self.sys.update_task_state(task_id, TaskState.FAILED)
            await self.sys.set_task_error(task_id, 
                f"Systematic framework compliance failure: {compliance_result.compliance_issues}")
        
        return {
            "status": "systematic_completion_processed",
            "framework_compliant": compliance_result.framework_compliant,
            "quality_acceptable": evaluation_result.quality_acceptable,
            "isolation_success_confirmed": compliance_result.isolation_success_validated
        }
```

#### 4. Systematic Resource Request Processes
**Framework-Aware Resource Addition**

```python
# systematic_need_more_context_process.py - Framework-aware context provision
class SystematicNeedMoreContextProcess:
    """Handles systematic context requests within established frameworks"""
    
    async def execute(self, requesting_task_id: int, context_request: str, justification: str = ""):
        requesting_task = await self.sys.get_task(requesting_task_id)
        systematic_framework = await self.sys.get_systematic_framework(requesting_task.systematic_framework_id)
        
        # PHASE 1: SYSTEMATIC FRAMEWORK VALIDATION
        framework_validation_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Validate context request within systematic framework boundaries",
            agent_type="request_validation",
            context=["request_validation_guide", "systematic_framework_validation_guide"],
            parameters={
                "context_request": context_request,
                "justification": justification,
                "systematic_framework": systematic_framework,
                "framework_context_boundaries": systematic_framework.context_boundaries,
                "isolation_requirements": systematic_framework.context_isolation_requirements
            }
        )
        
        await self.sys.wait_for_tasks([framework_validation_task_id])
        validation_result = await self.sys.get_task_result(framework_validation_task_id)
        
        if not validation_result.framework_compliant:
            await self.sys.add_system_message(
                requesting_task_id,
                f"Context request denied - not compliant with systematic framework: {validation_result.compliance_issues}"
            )
            await self.sys.update_task_state(requesting_task_id, TaskState.READY_FOR_AGENT)
            return {"status": "framework_non_compliant", "feedback": validation_result.compliance_issues}
        
        # PHASE 2: SYSTEMATIC CONTEXT PROVISION
        context_provision_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Provide systematic context within framework: {systematic_framework.domain_type}",
            agent_type="context_addition",
            context=["context_addition_guide", "systematic_framework_context_guide"],
            parameters={
                "context_request": context_request,
                "systematic_framework": systematic_framework,
                "framework_context_requirements": systematic_framework.context_standards,
                "isolation_context_needs": systematic_framework.isolation_context_requirements
            }
        )
        
        await self.sys.wait_for_tasks([context_provision_task_id])
        context_result = await self.sys.get_task_result(context_provision_task_id)
        
        # PHASE 3: SYSTEMATIC ISOLATION VALIDATION
        isolation_validation_task_id = await self.sys.create_subtask(
            parent_id=requesting_task_id,
            instruction=f"Validate isolation capability with additional context",
            agent_type="process_discovery",
            context=["isolation_validation_guide"],
            parameters={
                "additional_context": context_result.provided_context,
                "systematic_framework": systematic_framework,
                "updated_isolation_requirements": systematic_framework.enhanced_isolation_requirements
            }
        )
        
        await self.sys.wait_for_tasks([isolation_validation_task_id])
        isolation_result = await self.sys.get_task_result(isolation_validation_task_id)
        
        if isolation_result.isolation_capability_maintained:
            await self.sys.add_context_to_task(requesting_task_id, context_result.systematic_context_documents)
            await self.sys.update_task_state(requesting_task_id, TaskState.READY_FOR_AGENT)
            
            return {
                "status": "systematic_context_provided",
                "framework_compliant": True,
                "isolation_maintained": True,
                "context_documents": context_result.systematic_context_documents
            }
        else:
            await self.sys.add_system_message(
                requesting_task_id,
                f"Context provision would compromise isolation capability: {isolation_result.isolation_issues}"
            )
            return {"status": "isolation_compromise_prevented", "isolation_issues": isolation_result.isolation_issues}
```

## Core Systematic Functions Library

### Essential Systematic Process Functions
```python
class SystematicProcessFunctions:
    # Systematic Framework Management
    async def establish_systematic_framework(self, domain_type: str, framework_requirements: Dict) -> int:
        """Establish comprehensive systematic framework for domain before any execution"""
        
    async def validate_systematic_framework(self, framework_id: int, task_requirements: Dict) -> bool:
        """Validate systematic framework completeness for isolated task success"""
        
    async def get_systematic_framework(self, framework_id: int) -> SystematicFramework:
        """Retrieve complete systematic framework with all domain structure"""
        
    async def enhance_systematic_framework(self, framework_id: int, enhancement_data: Dict) -> bool:
        """Enhance systematic framework based on successful execution patterns"""
    
    # Systematic Task Lifecycle Management
    async def create_systematic_task(self, instruction: str, framework_id: int, **kwargs) -> int:
        """Create task within established systematic framework"""
        
    async def validate_isolation_capability(self, task_id: int, framework_id: int) -> bool:
        """Validate that task can succeed in isolation within systematic framework"""
        
    async def create_framework_compliant_subtask(self, parent_id: int, instruction: str, 
                                                framework_requirements: Dict, **kwargs) -> int:
        """Create subtask that complies with systematic framework boundaries"""
    
    # Systematic Process Orchestration
    async def execute_systematic_process(self, process_name: str, framework_id: int, **parameters) -> ProcessResult:
        """Execute systematic process within established framework boundaries"""
        
    async def validate_framework_compliance(self, task_id: int, framework_id: int, 
                                          compliance_criteria: Dict) -> ComplianceResult:
        """Validate systematic framework compliance during execution"""
        
    async def coordinate_framework_execution(self, framework_id: int, execution_plan: Dict) -> CoordinationResult:
        """Coordinate multiple systematic operations within framework boundaries"""
    
    # Systematic Resource Management
    async def assign_framework_appropriate_resources(self, task_id: int, framework_id: int, 
                                                   resource_requirements: Dict) -> ResourceAssignment:
        """Assign resources that comply with systematic framework boundaries"""
        
    async def validate_resource_framework_compliance(self, resource_assignment: ResourceAssignment, 
                                                   framework_id: int) -> bool:
        """Validate resource assignment maintains systematic framework compliance"""
        
    async def enhance_framework_resources(self, framework_id: int, resource_enhancements: Dict) -> bool:
        """Enhance systematic framework with additional compliant resources"""
```

## Key Systematic Design Principles

### 1. Systematic Framework Assignment Strategy
```python
# When any task is created:
def create_task(instruction: str, framework_id: int = None, **kwargs):
    if framework_id is None:
        # ALWAYS establish systematic framework first
        framework_id = execute_process("process_discovery_process", task_instruction=instruction)
    
    task_id = create_task_entity(instruction, systematic_framework_id=framework_id, **kwargs)
    execute_process("systematic_neutral_task_process", task_id=task_id)
    return task_id
```

### 2. Systematic Agent Tool Integration
Each agent has access to systematic framework-compliant tools:
- `break_down_task()` → triggers `SystematicBreakDownTaskProcess` (framework-compliant breakdown)
- `create_subtask()` → triggers `SystematicCreateSubtaskProcess` (framework-compliant creation)
- `end_task()` → triggers `SystematicEndTaskProcess` (framework-compliant completion)
- `need_more_context()` → triggers `SystematicNeedMoreContextProcess` (framework-aware context)
- `need_more_tools()` → triggers `SystematicNeedMoreToolsProcess` (framework-compliant tools)
- `need_process_establishment()` → triggers `ProcessDiscoveryProcess` (framework establishment)

### 3. Systematic Rolling Counter Integration
```python
# After every systematic framework operation:
counter_triggered = await sys.increment_counter(entity_type, entity_id, "systematic_usage")
if counter_triggered:
    await sys.execute_process("systematic_optimization_review",
                             entity_type=entity_type,
                             entity_id=entity_id,
                             systematic_framework_id=framework_id,
                             trigger_reason="systematic_usage_threshold")
```

### 4. Systematic Failure Recovery
```python
# Each systematic process includes framework-aware error handling:
try:
    result = await systematic_process_step()
except SystematicFrameworkError as e:
    if self.has_systematic_recovery_strategy(e):
        await self.execute_systematic_recovery_strategy(e)
    else:
        await sys.create_subtask(
            instruction=f"Recover systematic framework from: {e}",
            agent_type="recovery_agent",
            systematic_framework_id=self.get_recovery_framework_id()
        )
```

## Systematic Process Design Principles

### 1. **Framework-First Separation**
- **Systematic Processes**: Handle comprehensive domain analysis, framework establishment, and systematic coordination
- **Runtime**: Manages systematic LLM conversation flow and automatic task progression within established frameworks

### 2. **Systematic Framework Establishment Pattern**
All processes ensure comprehensive systematic framework before execution:

```python
# Standard pattern for systematic process implementation
class AnySystematicProcess:
    async def execute(self, **params):
        # 1. Validate systematic framework exists and is complete
        framework_validation = await self.validate_systematic_framework(params)
        if not framework_validation.complete:
            await self.establish_missing_framework_components(framework_validation.gaps)
        
        # 2. Create framework-compliant subtasks for systematic execution
        subtask_id = await self.sys.create_systematic_subtask(
            instruction="Systematic framework-compliant instruction",
            systematic_framework_id=framework_validation.framework_id,
            agent_type="appropriate_systematic_agent_type",
            context=["systematic_framework_context_documents"]
        )
        
        # 3. Validate isolation capability before execution
        isolation_validation = await self.validate_isolation_capability(subtask_id)
        if not isolation_validation.can_succeed_in_isolation:
            await self.enhance_isolation_capability(subtask_id, isolation_validation.gaps)
        
        # 4. Execute within systematic framework boundaries
        await self.sys.wait_for_tasks([subtask_id])
        result = await self.sys.get_task_result(subtask_id)
        
        # 5. Validate systematic framework compliance
        compliance_validation = await self.validate_framework_compliance(result)
        
        # Runtime automatically continues within systematic framework
```

### 3. **Systematic Tool Call Integration**
Agent tool calls trigger systematic framework-compliant processes:
- `break_down_task()` → `SystematicBreakDownTaskProcess` (framework-compliant breakdown)
- `end_task()` → `SystematicEndTaskProcess` (framework-compliant completion)
- `need_more_context()` → `SystematicNeedMoreContextProcess` (framework-aware context)
- `need_process_establishment()` → `ProcessDiscoveryProcess` (comprehensive framework establishment)

### 4. **Systematic Dependency Management**
Systematic processes set up framework-compliant dependencies; Runtime handles automatic continuation when systematic dependencies resolve within established framework boundaries.

This systematic architecture ensures comprehensive framework establishment precedes all execution and enables isolated task success through complete systematic structure establishment. The process-first approach transforms every undefined domain into systematic frameworks with rules, regulations, and comprehensive context for independent puzzle piece success.