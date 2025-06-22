"""
System Initialization Tasks

Defines the tasks that must be executed on first startup to initialize the system.
These tasks establish process frameworks, validate components, and prepare for autonomous operation.
"""

from typing import List, Dict, Any
from datetime import datetime


class InitializationTask:
    """Represents a system initialization task."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        instruction: str,
        agent_type: str,
        process: str,
        context: List[str],
        dependencies: List[str],
        success_criteria: List[str],
        deliverables: List[str],
        phase: int,
        priority: str = "high"
    ):
        self.task_id = task_id
        self.name = name
        self.instruction = instruction
        self.agent_type = agent_type
        self.process = process
        self.context = context
        self.dependencies = dependencies
        self.success_criteria = success_criteria
        self.deliverables = deliverables
        self.phase = phase
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for task creation."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "instruction": self.instruction,
            "agent_type": self.agent_type,
            "process": self.process,
            "context_documents": self.context,
            "dependencies": self.dependencies,
            "success_criteria": self.success_criteria,
            "deliverables": self.deliverables,
            "phase": self.phase,
            "priority": self.priority,
            "metadata": {
                "task_type": "initialization",
                "phase": self.phase,
                "task_id": self.task_id
            }
        }


# Define all initialization tasks
INITIALIZATION_TASKS = [
    # Phase 1: Bootstrap Validation (Tasks 1-3)
    InitializationTask(
        task_id="init_001",
        name="Bootstrap Knowledge System",
        instruction=(
            "Convert all existing documentation to knowledge entities and establish the initial knowledge base. "
            "This includes agent guides, architecture documents, system principles, and process documentation. "
            "Validate that all knowledge entities are properly structured and relationships are established."
        ),
        agent_type="documentation_agent",
        process="knowledge_bootstrap_process",
        context=["bootstrap_knowledge_conversion", "knowledge_entity_format", "knowledge_system_mvp_spec"],
        dependencies=[],
        success_criteria=[
            "All documentation converted to knowledge entities",
            "Knowledge entities stored in knowledge/ directory",
            "Entity relationships established",
            "Knowledge base statistics generated"
        ],
        deliverables=[
            "Knowledge entity files in JSON format",
            "Knowledge base statistics report",
            "Relationship validation results",
            "Bootstrap completion summary"
        ],
        phase=1
    ),
    
    InitializationTask(
        task_id="init_002",
        name="Test Context Assembly Engine",
        instruction=(
            "Validate that the context assembly engine can create complete context packages for tasks "
            "and detect when context is insufficient for isolated task success. Test with multiple "
            "agent types and task scenarios."
        ),
        agent_type="investigator_agent",
        process="context_system_validation",
        context=["knowledge_system_mvp_spec", "mvp_knowledge_implementation"],
        dependencies=["init_001"],
        success_criteria=[
            "Context packages assembled for each agent type",
            "Context completeness validation working",
            "Knowledge gap detection functional",
            "Context templates producing actionable guidance"
        ],
        deliverables=[
            "Context assembly test results",
            "Context completeness validation report",
            "Knowledge gap detection validation",
            "Context template effectiveness assessment"
        ],
        phase=1
    ),
    
    InitializationTask(
        task_id="init_003",
        name="Validate Entity Framework Operations",
        instruction=(
            "Test all core entity operations (CRUD, relationships, events) to ensure the entity "
            "framework is fully operational and can support systematic process execution."
        ),
        agent_type="investigator_agent",
        process="entity_system_validation",
        context=["entity_architecture", "database_schema_reference"],
        dependencies=["init_001"],
        success_criteria=[
            "All entity types can be created, read, updated, deleted",
            "Entity relationships tracked correctly",
            "Event logging captures all operations",
            "Entity validation prevents inconsistent states"
        ],
        deliverables=[
            "Entity operation test results",
            "Relationship tracking validation",
            "Event logging verification",
            "Entity consistency validation report"
        ],
        phase=1
    ),
    
    # Phase 2: Framework Establishment (Tasks 4-8)
    InitializationTask(
        task_id="init_004",
        name="Establish Process Discovery Framework",
        instruction=(
            "Create the systematic process discovery framework that will analyze task domains "
            "and establish comprehensive process frameworks before any task execution."
        ),
        agent_type="process_discovery",
        process="framework_establishment_process",
        context=["process_architecture", "process_discovery_guide"],
        dependencies=["init_002", "init_003"],
        success_criteria=[
            "Process discovery framework operational",
            "Domain analysis patterns established",
            "Framework establishment procedures created",
            "Isolation capability validation working"
        ],
        deliverables=[
            "Process discovery framework specification",
            "Domain analysis templates and procedures",
            "Framework establishment workflow",
            "Isolation validation methodology"
        ],
        phase=2
    ),
    
    InitializationTask(
        task_id="init_005",
        name="Create Core System Process Templates",
        instruction=(
            "Establish process templates for essential system operations: task breakdown, "
            "context addition, quality evaluation, and optimization review."
        ),
        agent_type="process_discovery",
        process="process_template_creation",
        context=["process_framework_guide", "agent_coordination_patterns"],
        dependencies=["init_004"],
        success_criteria=[
            "Task breakdown process template created",
            "Context addition process template created",
            "Quality evaluation process template created",
            "Optimization review process template created"
        ],
        deliverables=[
            "Core system process template library",
            "Process template documentation",
            "Process execution validation tests",
            "Process optimization guidelines"
        ],
        phase=2
    ),
    
    InitializationTask(
        task_id="init_006",
        name="Establish Agent Coordination Framework",
        instruction=(
            "Create systematic frameworks for agent coordination, communication, and workflow "
            "orchestration that enable complex multi-agent task execution."
        ),
        agent_type="feedback_agent",
        process="coordination_framework_establishment",
        context=["agent_coordination_guide", "workflow_design_patterns"],
        dependencies=["init_005"],
        success_criteria=[
            "Agent communication protocols established",
            "Workflow coordination patterns created",
            "Multi-agent orchestration framework operational",
            "Coordination quality metrics defined"
        ],
        deliverables=[
            "Agent coordination framework specification",
            "Communication protocol documentation",
            "Workflow orchestration patterns",
            "Coordination effectiveness metrics"
        ],
        phase=2
    ),
    
    InitializationTask(
        task_id="init_007",
        name="Establish Quality Assurance Framework",
        instruction=(
            "Create comprehensive quality assurance framework with evaluation criteria, "
            "success metrics, and continuous improvement mechanisms for all system operations."
        ),
        agent_type="task_evaluator",
        process="quality_framework_establishment",
        context=["quality_assurance_guide", "evaluation_methodologies"],
        dependencies=["init_006"],
        success_criteria=[
            "Quality evaluation criteria established for all entity types",
            "Success metrics defined and measurable",
            "Quality improvement feedback loops operational",
            "Quality trend analysis capabilities working"
        ],
        deliverables=[
            "Quality assurance framework specification",
            "Evaluation criteria for all system components",
            "Quality metrics and measurement procedures",
            "Quality improvement workflow"
        ],
        phase=2
    ),
    
    InitializationTask(
        task_id="init_008",
        name="Establish Knowledge Evolution Framework",
        instruction=(
            "Create framework for systematic knowledge evolution, including pattern recognition, "
            "knowledge creation from successful executions, and knowledge optimization based on usage patterns."
        ),
        agent_type="documentation_agent",
        process="knowledge_evolution_framework_establishment",
        context=["knowledge_management_guide", "learning_system_patterns"],
        dependencies=["init_007"],
        success_criteria=[
            "Knowledge evolution patterns established",
            "Automatic knowledge creation from successful executions",
            "Knowledge optimization based on usage analysis",
            "Knowledge gap detection and filling mechanisms"
        ],
        deliverables=[
            "Knowledge evolution framework specification",
            "Pattern recognition and knowledge creation workflows",
            "Knowledge optimization procedures",
            "Knowledge gap analysis and resolution system"
        ],
        phase=2
    ),
    
    # Phase 3: Capability Validation (Tasks 9-12)
    InitializationTask(
        task_id="init_009",
        name="Assess Current System Capabilities",
        instruction=(
            "Conduct comprehensive assessment of system capabilities across all domains "
            "and identify areas for capability enhancement and knowledge expansion."
        ),
        agent_type="investigator_agent",
        process="capability_assessment_process",
        context=["system_architecture_reference", "capability_evaluation_guide"],
        dependencies=["init_008"],
        success_criteria=[
            "Complete capability inventory created",
            "Capability gaps identified and prioritized",
            "Enhancement opportunities documented",
            "Capability development roadmap established"
        ],
        deliverables=[
            "System capability assessment report",
            "Capability gap analysis",
            "Enhancement opportunity prioritization",
            "Capability development roadmap"
        ],
        phase=3
    ),
    
    InitializationTask(
        task_id="init_010",
        name="Execute End-to-End System Test",
        instruction=(
            "Execute a complex, multi-domain task that tests all system components working together: "
            "process discovery, task breakdown, agent coordination, quality evaluation, and knowledge evolution."
        ),
        agent_type="agent_selector",
        process="system_integration_test",
        context=["system_operation_guide", "integration_test_patterns"],
        dependencies=["init_009"],
        success_criteria=[
            "Complex task successfully decomposed and executed",
            "All system components operated correctly",
            "Process frameworks established automatically",
            "Knowledge evolved from execution experience"
        ],
        deliverables=[
            "End-to-end test execution report",
            "System performance analysis",
            "Component integration validation",
            "Knowledge evolution verification"
        ],
        phase=3
    ),
    
    InitializationTask(
        task_id="init_011",
        name="Setup System Monitoring and Analytics",
        instruction=(
            "Establish comprehensive monitoring and analytics for system performance, "
            "entity effectiveness, process optimization, and knowledge evolution tracking."
        ),
        agent_type="optimizer_agent",
        process="monitoring_system_establishment",
        context=["monitoring_architecture_guide", "analytics_frameworks"],
        dependencies=["init_010"],
        success_criteria=[
            "Real-time system monitoring operational",
            "Performance analytics capturing key metrics",
            "Entity effectiveness tracking working",
            "Optimization opportunity detection active"
        ],
        deliverables=[
            "Monitoring and analytics system specification",
            "Performance dashboard and reporting",
            "Entity effectiveness tracking system",
            "Optimization opportunity detection system"
        ],
        phase=3
    ),
    
    InitializationTask(
        task_id="init_012",
        name="Establish Error Handling and Recovery Framework",
        instruction=(
            "Create comprehensive error handling and recovery framework that enables "
            "system resilience and learning from failures."
        ),
        agent_type="recovery_agent",
        process="recovery_framework_establishment",
        context=["recovery_agent_guide", "error_handling_patterns"],
        dependencies=["init_011"],
        success_criteria=[
            "Error detection and classification system operational",
            "Automatic recovery procedures established",
            "Failure analysis and learning mechanisms working",
            "System resilience validation complete"
        ],
        deliverables=[
            "Error handling and recovery framework specification",
            "Automatic recovery procedure library",
            "Failure analysis and learning system",
            "System resilience validation report"
        ],
        phase=3
    ),
    
    # Phase 4: Self-Improvement Setup (Tasks 13-15)
    InitializationTask(
        task_id="init_013",
        name="Initialize Optimization Review System",
        instruction=(
            "Activate the rolling review counter system and optimization review processes "
            "that enable continuous system improvement through usage-driven analysis."
        ),
        agent_type="optimizer_agent",
        process="optimization_system_initialization",
        context=["optimization_agent_guide", "rolling_review_system"],
        dependencies=["init_012"],
        success_criteria=[
            "Rolling review counters active for all entity types",
            "Optimization review processes operational",
            "Performance improvement detection working",
            "Systematic optimization cycles initiated"
        ],
        deliverables=[
            "Optimization review system configuration",
            "Rolling counter thresholds and triggers",
            "Optimization process validation",
            "Performance improvement tracking system"
        ],
        phase=4
    ),
    
    InitializationTask(
        task_id="init_014",
        name="Validate Self-Improvement Capabilities",
        instruction=(
            "Test and validate that the system can improve itself through process optimization, "
            "knowledge evolution, and capability enhancement based on usage patterns and performance analysis."
        ),
        agent_type="review_agent",
        process="self_improvement_validation",
        context=["self_improvement_guide", "system_evolution_patterns"],
        dependencies=["init_013"],
        success_criteria=[
            "System demonstrates measurable self-improvement",
            "Process optimization based on usage data working",
            "Knowledge evolution from execution patterns validated",
            "Capability enhancement through learning verified"
        ],
        deliverables=[
            "Self-improvement capability validation report",
            "Process optimization effectiveness analysis",
            "Knowledge evolution verification",
            "Capability enhancement documentation"
        ],
        phase=4
    ),
    
    InitializationTask(
        task_id="init_015",
        name="Certify System Readiness for Production Operation",
        instruction=(
            "Conduct final validation that the system is ready for autonomous operation, "
            "including all frameworks operational, knowledge base complete, and self-improvement mechanisms active."
        ),
        agent_type="review_agent",
        process="system_readiness_certification",
        context=["system_architecture_complete", "operational_readiness_criteria"],
        dependencies=["init_014"],
        success_criteria=[
            "All system frameworks operational and validated",
            "Knowledge base comprehensive and evolving",
            "Self-improvement mechanisms active and effective",
            "System ready for autonomous complex task execution"
        ],
        deliverables=[
            "System readiness certification report",
            "Operational capability confirmation",
            "Framework completeness validation",
            "Autonomous operation readiness declaration"
        ],
        phase=4
    )
]


def get_initialization_tasks() -> List[InitializationTask]:
    """Get all initialization tasks in order."""
    return INITIALIZATION_TASKS


def get_tasks_by_phase(phase: int) -> List[InitializationTask]:
    """Get initialization tasks for a specific phase."""
    return [task for task in INITIALIZATION_TASKS if task.phase == phase]


def get_task_by_id(task_id: str) -> InitializationTask:
    """Get a specific initialization task by ID."""
    for task in INITIALIZATION_TASKS:
        if task.task_id == task_id:
            return task
    return None


def get_phase_descriptions() -> Dict[int, str]:
    """Get descriptions for each initialization phase."""
    return {
        1: "Bootstrap Validation - Verify knowledge base and core components",
        2: "Framework Establishment - Create systematic process frameworks",
        3: "Capability Validation - Test system components and integration",
        4: "Self-Improvement Setup - Initialize optimization and learning"
    }