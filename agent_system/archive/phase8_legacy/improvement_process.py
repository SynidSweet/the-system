"""
Improvement Process - Handles self-improvement workflow.

This process is triggered when an improvement opportunity is identified
and orchestrates the validation, testing, and deployment of improvements.
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .base_process import BaseProcess, ProcessResult
from ..core.self_improvement_engine import (
    SelfImprovementEngine, 
    Improvement, 
    ImprovementType, 
    ImprovementStatus
)


class ImprovementProcess(BaseProcess):
    """
    Process for handling system improvements.
    
    This process:
    1. Validates improvement proposals
    2. Tests improvements in controlled environment
    3. Monitors effectiveness
    4. Deploys or rolls back based on results
    """
    
    async def execute(self, **kwargs) -> ProcessResult:
        """Execute the improvement process."""
        # Get improvement details
        improvement_type = kwargs.get('improvement_type')
        entity_type = kwargs.get('entity_type')
        entity_id = kwargs.get('entity_id')
        description = kwargs.get('description')
        rationale = kwargs.get('rationale')
        
        if not all([improvement_type, entity_type, entity_id, description]):
            return ProcessResult(
                success=False,
                error="Missing required improvement parameters"
            )
        
        try:
            # Create improvement object
            improvement = await self._create_improvement(
                improvement_type=improvement_type,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                rationale=rationale
            )
            
            # Log improvement proposal
            await self.log_event(
                event_type="IMPROVEMENT_PROPOSED",
                content=f"Proposed improvement: {description}",
                metadata={
                    "improvement_id": improvement.improvement_id,
                    "improvement_type": improvement_type,
                    "entity": f"{entity_type}_{entity_id}"
                }
            )
            
            # Validate improvement
            is_valid = await self._validate_improvement(improvement)
            
            if not is_valid:
                return ProcessResult(
                    success=False,
                    data={"improvement_id": improvement.improvement_id},
                    error="Improvement validation failed"
                )
            
            # Check safety constraints
            is_safe = await self._check_safety_constraints(improvement)
            
            if not is_safe:
                return ProcessResult(
                    success=False,
                    data={"improvement_id": improvement.improvement_id},
                    error="Improvement violates safety constraints"
                )
            
            # Deploy improvement for testing
            await self._deploy_for_testing(improvement)
            
            # Schedule effectiveness monitoring
            await self._schedule_monitoring(improvement)
            
            return ProcessResult(
                success=True,
                data={
                    "improvement_id": improvement.improvement_id,
                    "status": "testing",
                    "test_duration_hours": 24,
                    "expected_impact": improvement.expected_impact
                }
            )
            
        except Exception as e:
            await self.log_event(
                event_type="ERROR",
                content=f"Improvement process error: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )
            
            return ProcessResult(
                success=False,
                error=str(e)
            )
    
    async def _create_improvement(
        self,
        improvement_type: str,
        entity_type: str,
        entity_id: int,
        description: str,
        rationale: str
    ) -> Improvement:
        """Create improvement object with initial data."""
        # Get current performance metrics
        query = """
            SELECT 
                COUNT(*) as total_tasks,
                AVG(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_rate,
                AVG(CAST(metadata->>'$.duration' AS REAL)) as avg_duration,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as error_count
            FROM tasks
            WHERE agent_id = ? AND created_at > datetime('now', '-7 days')
        """
        
        metrics = None
        if entity_type == 'agent':
            result = await self.db.fetch_one(query, entity_id)
            if result:
                metrics = {
                    "total_tasks": result['total_tasks'],
                    "success_rate": result['success_rate'] or 0,
                    "avg_duration": result['avg_duration'] or 0,
                    "error_rate": result['error_count'] / max(result['total_tasks'], 1)
                }
        
        # Create improvement
        imp_type = ImprovementType(improvement_type)
        
        improvement = Improvement(
            improvement_id=f"proc_{entity_type}_{entity_id}_{datetime.utcnow().timestamp()}",
            improvement_type=imp_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            rationale=rationale,
            expected_impact=self._estimate_impact(imp_type),
            changes={},
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow(),
            metrics_before=metrics
        )
        
        return improvement
    
    def _estimate_impact(self, improvement_type: ImprovementType) -> Dict[str, Any]:
        """Estimate expected impact based on improvement type."""
        impact_estimates = {
            ImprovementType.INSTRUCTION_UPDATE: {
                "success_rate_improvement": 0.1,
                "clarity_improvement": 0.3
            },
            ImprovementType.CONTEXT_OPTIMIZATION: {
                "performance_gain": 0.2,
                "context_reduction": 0.3
            },
            ImprovementType.TOOL_REASSIGNMENT: {
                "efficiency_gain": 0.25,
                "error_reduction": 0.15
            },
            ImprovementType.PROCESS_AUTOMATION: {
                "speed_improvement": 0.5,
                "consistency_improvement": 0.8
            },
            ImprovementType.PERFORMANCE_TUNING: {
                "performance_gain": 0.4,
                "resource_efficiency": 0.3
            },
            ImprovementType.ERROR_PREVENTION: {
                "error_reduction": 0.6,
                "reliability_improvement": 0.5
            }
        }
        
        return impact_estimates.get(improvement_type, {"general_improvement": 0.2})
    
    async def _validate_improvement(self, improvement: Improvement) -> bool:
        """Validate improvement feasibility and safety."""
        # Check entity exists and is active
        entity = await self.get_entity(improvement.entity_type, improvement.entity_id)
        
        if not entity or entity.get('state') != 'active':
            return False
        
        # Check no other improvements are active for this entity
        active_count = await self.db.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM improvement_history
            WHERE entity_type = ? 
              AND entity_id = ?
              AND status IN ('testing', 'validated')
            """,
            improvement.entity_type,
            improvement.entity_id
        )
        
        if active_count and active_count['count'] > 0:
            return False
        
        # Validate specific improvement type requirements
        if improvement.improvement_type == ImprovementType.INSTRUCTION_UPDATE:
            # Must have sufficient task history
            task_count = await self.db.fetch_one(
                "SELECT COUNT(*) as count FROM tasks WHERE agent_id = ?",
                improvement.entity_id
            )
            if not task_count or task_count['count'] < 50:
                return False
        
        elif improvement.improvement_type == ImprovementType.TOOL_REASSIGNMENT:
            # Must have tool usage data
            tool_usage = await self.db.fetch_one(
                """
                SELECT COUNT(*) as count 
                FROM tool_usage_events 
                WHERE entity_type = ? AND entity_id = ?
                """,
                improvement.entity_type,
                improvement.entity_id
            )
            if not tool_usage or tool_usage['count'] < 20:
                return False
        
        return True
    
    async def _check_safety_constraints(self, improvement: Improvement) -> bool:
        """Check if improvement violates safety constraints."""
        # Get system-wide improvement statistics
        stats = await self.db.fetch_one(
            """
            SELECT 
                COUNT(*) as total_recent,
                SUM(CASE WHEN status = 'rolled_back' THEN 1 ELSE 0 END) as rollbacks,
                AVG(effectiveness) as avg_effectiveness
            FROM improvement_history
            WHERE created_at > datetime('now', '-24 hours')
            """
        )
        
        if stats:
            # Check rollback rate
            if stats['total_recent'] > 0:
                rollback_rate = stats['rollbacks'] / stats['total_recent']
                if rollback_rate > 0.3:  # 30% rollback rate
                    return False
            
            # Check if system is in degraded state
            if stats['avg_effectiveness'] and stats['avg_effectiveness'] < -0.1:
                return False
        
        # Check entity-specific constraints
        entity_config = await self.db.fetch_one(
            """
            SELECT improvement_config
            FROM entities
            WHERE entity_type = ? AND entity_id = ?
            """,
            improvement.entity_type,
            improvement.entity_id
        )
        
        if entity_config and entity_config['improvement_config']:
            config = json.loads(entity_config['improvement_config'])
            if not config.get('auto_improve_enabled', True):
                return False
        
        return True
    
    async def _deploy_for_testing(self, improvement: Improvement):
        """Deploy improvement in testing mode."""
        # Store improvement in history
        await self.db.execute(
            """
            INSERT INTO improvement_history 
            (improvement_id, improvement_type, entity_type, entity_id,
             description, status, metrics_before, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            improvement.improvement_id,
            improvement.improvement_type.value,
            improvement.entity_type,
            improvement.entity_id,
            improvement.description,
            ImprovementStatus.TESTING.value,
            json.dumps(improvement.metrics_before) if improvement.metrics_before else None,
            improvement.created_at
        )
        
        # Apply changes based on improvement type
        if improvement.improvement_type == ImprovementType.INSTRUCTION_UPDATE:
            await self._apply_instruction_update(improvement)
        elif improvement.improvement_type == ImprovementType.CONTEXT_OPTIMIZATION:
            await self._apply_context_optimization(improvement)
        elif improvement.improvement_type == ImprovementType.PERFORMANCE_TUNING:
            await self._apply_performance_tuning(improvement)
        
        # Log deployment
        await self.log_event(
            event_type="IMPROVEMENT_DEPLOYED",
            content=f"Deployed improvement for testing: {improvement.description}",
            metadata={
                "improvement_id": improvement.improvement_id,
                "test_mode": True
            }
        )
    
    async def _apply_instruction_update(self, improvement: Improvement):
        """Apply instruction update to agent."""
        if improvement.entity_type != 'agent':
            return
        
        # Get current instructions
        agent = await self.db.fetch_one(
            "SELECT instruction FROM agents WHERE id = ?",
            improvement.entity_id
        )
        
        if not agent:
            return
        
        # Generate improved instructions
        # In a real system, this might use an LLM to improve instructions
        improved = agent['instruction'] + "\n\n[Testing improvement: Enhanced clarity and specificity]"
        
        # Update with testing flag
        await self.db.execute(
            """
            UPDATE agents 
            SET instruction = ?,
                metadata = json_set(metadata, '$.testing_improvement', ?)
            WHERE id = ?
            """,
            improved,
            improvement.improvement_id,
            improvement.entity_id
        )
        
        # Store original for rollback
        improvement.rollback_data = {"original_instruction": agent['instruction']}
    
    async def _apply_context_optimization(self, improvement: Improvement):
        """Apply context optimization."""
        if improvement.entity_type != 'agent':
            return
        
        # Get current context
        agent = await self.db.fetch_one(
            "SELECT context_documents FROM agents WHERE id = ?",
            improvement.entity_id
        )
        
        if not agent:
            return
        
        contexts = json.loads(agent['context_documents'])
        
        # Remove least used contexts (simplified)
        if len(contexts) > 5:
            optimized = contexts[:5]  # Keep top 5
            
            await self.db.execute(
                "UPDATE agents SET context_documents = ? WHERE id = ?",
                json.dumps(optimized),
                improvement.entity_id
            )
            
            improvement.rollback_data = {"original_contexts": contexts}
    
    async def _apply_performance_tuning(self, improvement: Improvement):
        """Apply performance tuning."""
        # Update entity metadata with performance flags
        await self.db.execute(
            """
            UPDATE entities
            SET metadata = json_set(
                metadata,
                '$.performance_mode', true,
                '$.cache_enabled', true,
                '$.batch_size', 10
            )
            WHERE entity_type = ? AND entity_id = ?
            """,
            improvement.entity_type,
            improvement.entity_id
        )
    
    async def _schedule_monitoring(self, improvement: Improvement):
        """Schedule effectiveness monitoring for the improvement."""
        # Create a monitoring task
        monitoring_task = {
            "instruction": f"Monitor improvement effectiveness: {improvement.improvement_id}",
            "metadata": {
                "improvement_id": improvement.improvement_id,
                "check_after": datetime.utcnow().timestamp() + (24 * 3600),  # 24 hours
                "process": "improvement_monitoring"
            }
        }
        
        # In a real system, this would schedule the monitoring task
        await self.log_event(
            event_type="SYSTEM_EVENT",
            content="Scheduled improvement monitoring",
            metadata=monitoring_task
        )


class ImprovementMonitoringProcess(BaseProcess):
    """
    Process for monitoring improvement effectiveness.
    
    This process runs after the test period to evaluate
    whether an improvement should be kept or rolled back.
    """
    
    async def execute(self, **kwargs) -> ProcessResult:
        """Monitor and evaluate improvement effectiveness."""
        improvement_id = kwargs.get('improvement_id')
        
        if not improvement_id:
            return ProcessResult(
                success=False,
                error="Missing improvement_id"
            )
        
        try:
            # Get improvement details
            improvement = await self.db.fetch_one(
                """
                SELECT * FROM improvement_history
                WHERE improvement_id = ? AND status = 'testing'
                """,
                improvement_id
            )
            
            if not improvement:
                return ProcessResult(
                    success=False,
                    error="Improvement not found or not in testing"
                )
            
            # Get current metrics
            current_metrics = await self._get_current_metrics(
                improvement['entity_type'],
                improvement['entity_id']
            )
            
            # Calculate effectiveness
            effectiveness = self._calculate_effectiveness(
                json.loads(improvement['metrics_before']) if improvement['metrics_before'] else {},
                current_metrics
            )
            
            # Decide whether to keep or rollback
            if effectiveness >= 0:  # Positive or neutral impact
                await self._finalize_improvement(improvement, current_metrics, effectiveness)
                result = "deployed"
            else:  # Negative impact
                await self._rollback_improvement(improvement, current_metrics, effectiveness)
                result = "rolled_back"
            
            return ProcessResult(
                success=True,
                data={
                    "improvement_id": improvement_id,
                    "result": result,
                    "effectiveness": effectiveness
                }
            )
            
        except Exception as e:
            await self.log_event(
                event_type="ERROR",
                content=f"Improvement monitoring error: {str(e)}",
                metadata={"improvement_id": improvement_id}
            )
            
            return ProcessResult(
                success=False,
                error=str(e)
            )
    
    async def _get_current_metrics(
        self, 
        entity_type: str, 
        entity_id: int
    ) -> Dict[str, Any]:
        """Get current performance metrics."""
        if entity_type == 'agent':
            result = await self.db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_tasks,
                    AVG(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_rate,
                    AVG(CAST(metadata->>'$.duration' AS REAL)) as avg_duration,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as error_count
                FROM tasks
                WHERE agent_id = ? 
                  AND created_at > datetime('now', '-24 hours')
                """,
                entity_id
            )
            
            if result:
                return {
                    "total_tasks": result['total_tasks'],
                    "success_rate": result['success_rate'] or 0,
                    "avg_duration": result['avg_duration'] or 0,
                    "error_rate": result['error_count'] / max(result['total_tasks'], 1)
                }
        
        return {}
    
    def _calculate_effectiveness(
        self, 
        before: Dict[str, Any], 
        after: Dict[str, Any]
    ) -> float:
        """Calculate improvement effectiveness."""
        if not before or not after:
            return 0.0
        
        scores = []
        
        # Compare metrics
        if 'success_rate' in before and 'success_rate' in after:
            improvement = (after['success_rate'] - before['success_rate']) / max(1 - before['success_rate'], 0.01)
            scores.append(improvement)
        
        if 'error_rate' in before and 'error_rate' in after:
            improvement = (before['error_rate'] - after['error_rate']) / max(before['error_rate'], 0.01)
            scores.append(improvement)
        
        if 'avg_duration' in before and 'avg_duration' in after:
            improvement = (before['avg_duration'] - after['avg_duration']) / max(before['avg_duration'], 0.01)
            scores.append(improvement * 0.5)  # Weight performance less
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def _finalize_improvement(
        self, 
        improvement: Dict[str, Any],
        current_metrics: Dict[str, Any],
        effectiveness: float
    ):
        """Finalize successful improvement."""
        # Update improvement record
        await self.db.execute(
            """
            UPDATE improvement_history
            SET status = 'deployed',
                effectiveness = ?,
                metrics_after = ?,
                evaluated_at = CURRENT_TIMESTAMP
            WHERE improvement_id = ?
            """,
            effectiveness,
            json.dumps(current_metrics),
            improvement['improvement_id']
        )
        
        # Remove testing flag
        if improvement['entity_type'] == 'agent':
            await self.db.execute(
                """
                UPDATE agents
                SET metadata = json_remove(metadata, '$.testing_improvement')
                WHERE id = ?
                """,
                improvement['entity_id']
            )
        
        # Log success
        await self.log_event(
            event_type="IMPROVEMENT_EVALUATED",
            content=f"Improvement successful: {effectiveness:.2%} effectiveness",
            metadata={
                "improvement_id": improvement['improvement_id'],
                "effectiveness": effectiveness
            }
        )
    
    async def _rollback_improvement(
        self, 
        improvement: Dict[str, Any],
        current_metrics: Dict[str, Any],
        effectiveness: float
    ):
        """Rollback unsuccessful improvement."""
        # Update improvement record
        await self.db.execute(
            """
            UPDATE improvement_history
            SET status = 'rolled_back',
                effectiveness = ?,
                metrics_after = ?,
                evaluated_at = CURRENT_TIMESTAMP
            WHERE improvement_id = ?
            """,
            effectiveness,
            json.dumps(current_metrics),
            improvement['improvement_id']
        )
        
        # Rollback changes based on type
        if improvement['improvement_type'] == 'instruction_update':
            # Restore original instructions
            # (In real system, would restore from rollback_data)
            pass
        
        # Log rollback
        await self.log_event(
            event_type="IMPROVEMENT_ROLLED_BACK",
            content=f"Improvement rolled back: {effectiveness:.2%} effectiveness",
            metadata={
                "improvement_id": improvement['improvement_id'],
                "effectiveness": effectiveness
            }
        )