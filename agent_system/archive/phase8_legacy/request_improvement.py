"""
Tool for agents to request system improvements.

This tool allows agents to identify and propose improvements
based on their experiences and observations.
"""

from typing import Dict, Any, Optional
import json

from ..tools import Tool, tool_registry
from ..core.models import ToolResult
from ..database.models import Task


class RequestImprovementTool(Tool):
    """
    Tool that allows agents to request system improvements.
    
    Agents can use this to:
    - Report recurring issues
    - Suggest optimizations
    - Request new capabilities
    - Propose process improvements
    """
    
    name = "request_improvement"
    description = """Request a system improvement based on observations or needs.
    
    Use this tool when you:
    - Encounter recurring errors or inefficiencies
    - Identify opportunities for optimization
    - Need new capabilities or tools
    - Notice patterns that could be automated
    
    Parameters:
    - improvement_type: Type of improvement (instruction_update, context_optimization, 
      tool_reassignment, process_automation, performance_tuning, error_prevention)
    - description: Clear description of the improvement needed
    - rationale: Explanation of why this improvement would help
    - evidence: Optional data or examples supporting the request
    """
    
    parameters = {
        "improvement_type": {
            "type": "string",
            "description": "Type of improvement",
            "enum": [
                "instruction_update",
                "context_optimization", 
                "tool_reassignment",
                "process_automation",
                "performance_tuning",
                "error_prevention"
            ],
            "required": True
        },
        "description": {
            "type": "string",
            "description": "Clear description of the improvement",
            "required": True
        },
        "rationale": {
            "type": "string",
            "description": "Why this improvement would help",
            "required": True
        },
        "evidence": {
            "type": "object",
            "description": "Supporting data or examples",
            "required": False
        }
    }
    
    async def execute(
        self,
        task: Task,
        improvement_type: str,
        description: str,
        rationale: str,
        evidence: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        """Execute improvement request."""
        try:
            # Get the agent making the request
            agent_id = task.agent_id
            
            # Check if this is a duplicate request
            recent_similar = await self.db.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM optimization_opportunities
                WHERE entity_type = 'agent'
                  AND entity_id = ?
                  AND opportunity_type = ?
                  AND description LIKE ?
                  AND created_at > datetime('now', '-24 hours')
                """,
                agent_id,
                improvement_type,
                f"%{description[:50]}%"
            )
            
            if recent_similar and recent_similar['count'] > 0:
                return ToolResult(
                    success=True,
                    data={
                        "status": "duplicate",
                        "message": "Similar improvement already requested recently"
                    }
                )
            
            # Calculate confidence score based on agent's track record
            agent_stats = await self.db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_tasks,
                    AVG(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_rate,
                    COUNT(DISTINCT DATE(created_at)) as days_active
                FROM tasks
                WHERE agent_id = ?
                """,
                agent_id
            )
            
            # Base confidence on agent experience and success rate
            confidence = 0.5  # Base confidence
            if agent_stats:
                if agent_stats['total_tasks'] > 100:
                    confidence += 0.2
                if agent_stats['success_rate'] > 0.8:
                    confidence += 0.2
                if agent_stats['days_active'] > 7:
                    confidence += 0.1
            
            # Determine impact based on improvement type
            impact_map = {
                "error_prevention": "high",
                "performance_tuning": "high",
                "process_automation": "high",
                "tool_reassignment": "medium",
                "context_optimization": "medium",
                "instruction_update": "low"
            }
            impact = impact_map.get(improvement_type, "medium")
            
            # Create optimization opportunity
            opportunity_id = await self.db.execute(
                """
                INSERT INTO optimization_opportunities
                (entity_type, entity_id, opportunity_type, description,
                 potential_impact, confidence_score, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                "agent",
                agent_id,
                improvement_type,
                description,
                impact,
                confidence,
                "pending",
                json.dumps({
                    "rationale": rationale,
                    "evidence": evidence,
                    "requested_by_task": task.id,
                    "agent_requested": True
                })
            )
            
            # Log the request
            await self.event_manager.log_event(
                event_type="OPTIMIZATION_DISCOVERED",
                entity_type="agent",
                entity_id=agent_id,
                content=f"Agent requested improvement: {description}",
                metadata={
                    "opportunity_id": opportunity_id,
                    "improvement_type": improvement_type,
                    "confidence": confidence
                }
            )
            
            # If high confidence and impact, trigger immediate review
            if confidence >= 0.8 and impact == "high":
                # Create improvement task
                from ..processes.improvement_process import ImprovementProcess
                
                process_task = await self.db.execute(
                    """
                    INSERT INTO tasks
                    (instruction, agent_id, status, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    f"Process improvement request: {description}",
                    agent_id,  # Assign to requesting agent for now
                    "pending",
                    json.dumps({
                        "process": "improvement",
                        "improvement_type": improvement_type,
                        "description": description,
                        "rationale": rationale,
                        "auto_triggered": True
                    })
                )
                
                return ToolResult(
                    success=True,
                    data={
                        "status": "triggered",
                        "opportunity_id": opportunity_id,
                        "task_id": process_task,
                        "message": "High-priority improvement triggered for immediate review"
                    }
                )
            
            return ToolResult(
                success=True,
                data={
                    "status": "queued",
                    "opportunity_id": opportunity_id,
                    "confidence_score": confidence,
                    "impact": impact,
                    "message": f"Improvement request queued for review (confidence: {confidence:.2f})"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to request improvement: {str(e)}"
            )


# Register the tool
tool_registry.register("request_improvement", RequestImprovementTool)