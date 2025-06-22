"""
Process Discovery Process - The systematic framework establishment process applied to every task.

This process ensures comprehensive framework analysis and establishment before any task execution,
transforming undefined problems into systematic domains with complete structural support.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models import Task, TaskState, Agent, Process, Document
from ..core.process_base import ProcessBase
from ..core.process_result import ProcessResult


class ProcessDiscoveryProcess(ProcessBase):
    """
    Systematic process applied to every task for comprehensive framework establishment before execution.
    
    This is the PRIMARY process in the process-first architecture - it ensures that every task
    operates within established systematic frameworks rather than ad-hoc approaches.
    """
    
    process_name = "process_discovery_process"
    process_description = "Analyzes task domains and establishes comprehensive systematic frameworks before any execution"
    
    async def execute(self, task_id: int) -> ProcessResult:
        """Execute comprehensive process discovery and framework establishment."""
        task = await self.sys.get_task(task_id)
        
        # PHASE 1: COMPREHENSIVE DOMAIN ANALYSIS (ALWAYS FIRST)
        self.logger.info(f"Starting domain analysis for task {task_id}: {task.instruction}")
        
        domain_analysis_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Analyze domain structure requirements for: {task.instruction}",
            agent_type="process_discovery",
            context=["process_discovery_guide", "domain_analysis_patterns"],
            process="domain_analysis_process",
            parameters={
                "original_instruction": task.instruction,
                "task_context": task.additional_context,
                "parent_task_id": task_id
            }
        )
        
        await self.sys.wait_for_tasks([domain_analysis_task_id])
        domain_analysis = await self.sys.get_task_result(domain_analysis_task_id)
        
        if not domain_analysis or not domain_analysis.get("domain_type"):
            return ProcessResult(
                success=False,
                error="Domain analysis failed to identify domain type",
                data={"task_id": task_id}
            )
        
        # PHASE 2: SYSTEMATIC PROCESS FRAMEWORK IDENTIFICATION
        self.logger.info(f"Identifying process gaps for domain: {domain_analysis['domain_type']}")
        
        # Get existing processes for this domain
        existing_processes = await self._get_applicable_processes(domain_analysis["domain_type"])
        
        process_gap_analysis_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction=f"Identify missing systematic processes for domain: {domain_analysis['domain_type']}",
            agent_type="process_discovery",
            context=["process_framework_library", "systematic_process_patterns"],
            parameters={
                "domain_analysis": domain_analysis,
                "required_systematic_structure": domain_analysis.get("framework_requirements", {}),
                "existing_processes": [p.to_dict() for p in existing_processes]
            }
        )
        
        await self.sys.wait_for_tasks([process_gap_analysis_task_id])
        process_gaps = await self.sys.get_task_result(process_gap_analysis_task_id)
        
        # PHASE 3: SYSTEMATIC FRAMEWORK ESTABLISHMENT (BEFORE ANY EXECUTION)
        if process_gaps and process_gaps.get("missing_critical_processes"):
            self.logger.info(f"Establishing {len(process_gaps['missing_critical_processes'])} missing frameworks")
            
            framework_creation_tasks = []
            
            for missing_process in process_gaps["missing_critical_processes"]:
                creation_task_id = await self.sys.create_subtask(
                    parent_id=task_id,
                    instruction=f"Establish systematic process framework: {missing_process['name']}",
                    agent_type="process_discovery",
                    context=["process_creation_guide", "systematic_framework_patterns"],
                    parameters={
                        "process_specification": missing_process,
                        "domain_context": domain_analysis,
                        "isolation_requirements": missing_process.get("isolated_task_success_requirements", {})
                    }
                )
                framework_creation_tasks.append(creation_task_id)
            
            # Wait for ALL systematic frameworks to be established
            await self.sys.wait_for_tasks(framework_creation_tasks)
            
            # Verify all frameworks were created successfully
            for task_id in framework_creation_tasks:
                result = await self.sys.get_task_result(task_id)
                if not result or not result.get("success"):
                    self.logger.error(f"Framework creation failed for task {task_id}")
        
        # PHASE 4: SYSTEMATIC FRAMEWORK VALIDATION
        self.logger.info("Validating systematic framework completeness")
        
        # Re-fetch processes after creation
        all_processes = await self._get_applicable_processes(domain_analysis["domain_type"])
        
        framework_validation_task_id = await self.sys.create_subtask(
            parent_id=task_id,
            instruction="Validate systematic framework completeness for isolated task success",
            agent_type="process_discovery",
            context=["framework_validation_guide"],
            parameters={
                "established_frameworks": [p.to_dict() for p in all_processes],
                "isolation_requirements": domain_analysis.get("isolated_task_requirements", {}),
                "domain_completeness_criteria": domain_analysis.get("systematic_completeness_requirements", {})
            }
        )
        
        await self.sys.wait_for_tasks([framework_validation_task_id])
        validation_result = await self.sys.get_task_result(framework_validation_task_id)
        
        if not validation_result or not validation_result.get("framework_complete"):
            # Framework incomplete - establish additional systematic structure
            if validation_result and validation_result.get("completeness_gaps"):
                await self._establish_additional_framework(task_id, validation_result["completeness_gaps"])
            else:
                self.logger.warning("Framework validation incomplete but no specific gaps identified")
        
        # PHASE 5: SYSTEMATIC TASK PREPARATION (ONLY AFTER COMPLETE FRAMEWORK)
        primary_process = validation_result.get("primary_systematic_process", "systematic_neutral_task_process")
        framework_docs = validation_result.get("systematic_framework_documentation", [])
        
        # Update task with systematic framework information
        await self.sys.update_task(
            task_id,
            process=primary_process,
            additional_context=framework_docs,
            metadata={
                "systematic_framework_id": validation_result.get("framework_id"),
                "domain_type": domain_analysis["domain_type"],
                "isolation_capability": validation_result.get("isolation_capability", False)
            }
        )
        
        # Update task state to indicate framework establishment is complete
        await self.sys.update_task_state(task_id, TaskState.READY_FOR_AGENT)
        
        return ProcessResult(
            success=True,
            data={
                "systematic_framework_established": True,
                "domain_type": domain_analysis["domain_type"],
                "framework_id": validation_result.get("framework_id"),
                "isolated_task_success_enabled": validation_result.get("isolation_capability", False),
                "primary_process": primary_process,
                "framework_documentation": framework_docs
            }
        )
    
    async def _get_applicable_processes(self, domain_type: str) -> List[Process]:
        """Get all processes applicable to a domain type."""
        # Query processes that match the domain
        all_processes = await self.sys.query_entities(
            entity_type="process",
            filters={"status": "active"}
        )
        
        # Filter processes relevant to this domain
        applicable = []
        for process in all_processes:
            # Check if process metadata indicates domain relevance
            if process.metadata:
                domains = process.metadata.get("applicable_domains", [])
                if domain_type in domains or "universal" in domains:
                    applicable.append(process)
            
            # Also check if domain is mentioned in process name or description
            if domain_type.lower() in process.name.lower() or \
               (process.description and domain_type.lower() in process.description.lower()):
                if process not in applicable:
                    applicable.append(process)
        
        return applicable
    
    async def _establish_additional_framework(self, task_id: int, completeness_gaps: List[Dict]):
        """Establish additional framework components for identified gaps."""
        self.logger.info(f"Establishing additional framework components for {len(completeness_gaps)} gaps")
        
        gap_tasks = []
        for gap in completeness_gaps:
            gap_task_id = await self.sys.create_subtask(
                parent_id=task_id,
                instruction=f"Establish framework component: {gap.get('description', 'Unknown gap')}",
                agent_type="process_discovery",
                context=["process_creation_guide", "framework_enhancement_guide"],
                parameters={
                    "gap_specification": gap,
                    "gap_type": gap.get("type", "unknown"),
                    "requirements": gap.get("requirements", {})
                }
            )
            gap_tasks.append(gap_task_id)
        
        if gap_tasks:
            await self.sys.wait_for_tasks(gap_tasks)