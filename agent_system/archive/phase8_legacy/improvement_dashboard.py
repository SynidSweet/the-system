"""
Self-Improvement Dashboard API endpoints.

Provides real-time monitoring of system self-improvement activities.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from ..database.db_manager import DatabaseManager
from ..core.self_improvement_engine import SelfImprovementEngine, ImprovementStatus
from .auth import get_current_user


router = APIRouter(prefix="/api/improvements", tags=["improvements"])


async def get_db():
    """Dependency to get database manager."""
    # This would be properly initialized in production
    from ..database.db_manager import DatabaseManager
    db = DatabaseManager()
    await db.initialize()
    return db


async def get_improvement_engine(db: DatabaseManager = Depends(get_db)):
    """Dependency to get improvement engine."""
    from ..core.event_manager import EventManager
    event_manager = EventManager(db)
    return SelfImprovementEngine(db, event_manager)


@router.get("/status")
async def get_improvement_status(
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get overall self-improvement system status."""
    # Get summary metrics
    metrics = await db.fetch_one(
        """
        SELECT 
            COUNT(DISTINCT entity_type || '_' || entity_id) as entities_improved,
            COUNT(*) as total_improvements,
            SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed,
            SUM(CASE WHEN status = 'rolled_back' THEN 1 ELSE 0 END) as rolled_back,
            SUM(CASE WHEN status = 'testing' THEN 1 ELSE 0 END) as in_testing,
            AVG(effectiveness) as avg_effectiveness,
            MAX(created_at) as last_improvement
        FROM improvement_history
        """
    )
    
    # Get pending opportunities
    opportunities = await db.fetch_one(
        """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN potential_impact = 'high' THEN 1 ELSE 0 END) as high_impact,
            SUM(CASE WHEN potential_impact = 'medium' THEN 1 ELSE 0 END) as medium_impact,
            SUM(CASE WHEN potential_impact = 'low' THEN 1 ELSE 0 END) as low_impact
        FROM optimization_opportunities
        WHERE status = 'pending'
        """
    )
    
    # Get pending reviews
    reviews = await db.fetch_one(
        """
        SELECT COUNT(*) as pending_reviews
        FROM rolling_review_counters rrc
        JOIN entities e ON rrc.entity_id = e.entity_id AND rrc.entity_type = e.entity_type
        WHERE e.state = 'active'
          AND (
            (rrc.review_trigger_type = 'threshold' AND rrc.task_count >= rrc.review_interval)
            OR
            (rrc.review_trigger_type = 'periodic' 
             AND datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now'))
          )
        """
    )
    
    return {
        "status": "active",
        "metrics": dict(metrics) if metrics else {},
        "opportunities": dict(opportunities) if opportunities else {},
        "pending_reviews": reviews['pending_reviews'] if reviews else 0,
        "system_health": _calculate_system_health(metrics, opportunities)
    }


@router.get("/active")
async def get_active_improvements(
    engine: SelfImprovementEngine = Depends(get_improvement_engine),
    current_user: Dict = Depends(get_current_user)
):
    """Get currently active improvements."""
    active = []
    
    for imp_id, improvement in engine.active_improvements.items():
        active.append({
            "improvement_id": improvement.improvement_id,
            "type": improvement.improvement_type.value,
            "entity": f"{improvement.entity_type}_{improvement.entity_id}",
            "description": improvement.description,
            "status": improvement.status.value,
            "deployed_at": improvement.deployed_at.isoformat() if improvement.deployed_at else None,
            "expected_impact": improvement.expected_impact
        })
    
    return {
        "active_improvements": active,
        "count": len(active),
        "max_concurrent": engine.max_concurrent_improvements
    }


@router.get("/history")
async def get_improvement_history(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get improvement history with optional filters."""
    query = """
        SELECT 
            ih.*,
            e.name as entity_name
        FROM improvement_history ih
        JOIN entities e ON ih.entity_type = e.entity_type AND ih.entity_id = e.entity_id
        WHERE 1=1
    """
    params = []
    
    if entity_type:
        query += " AND ih.entity_type = ?"
        params.append(entity_type)
    
    if entity_id is not None:
        query += " AND ih.entity_id = ?"
        params.append(entity_id)
    
    if status:
        query += " AND ih.status = ?"
        params.append(status)
    
    query += " ORDER BY ih.created_at DESC LIMIT ?"
    params.append(limit)
    
    improvements = await db.fetch_all(query, *params)
    
    return {
        "improvements": [_format_improvement(imp) for imp in improvements],
        "count": len(improvements)
    }


@router.get("/analytics")
async def get_improvement_analytics(
    hours: int = 168,  # Default to 1 week
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get improvement analytics and trends."""
    # Get improvements by type
    by_type = await db.fetch_all(
        """
        SELECT 
            improvement_type,
            COUNT(*) as count,
            AVG(effectiveness) as avg_effectiveness,
            SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed,
            SUM(CASE WHEN status = 'rolled_back' THEN 1 ELSE 0 END) as rolled_back
        FROM improvement_history
        WHERE created_at > datetime('now', '-' || ? || ' hours')
        GROUP BY improvement_type
        """,
        hours
    )
    
    # Get improvements by entity
    by_entity = await db.fetch_all(
        """
        SELECT 
            ih.entity_type,
            ih.entity_id,
            e.name as entity_name,
            COUNT(*) as improvement_count,
            AVG(ih.effectiveness) as avg_effectiveness,
            MAX(ih.created_at) as last_improvement
        FROM improvement_history ih
        JOIN entities e ON ih.entity_type = e.entity_type AND ih.entity_id = e.entity_id
        WHERE ih.created_at > datetime('now', '-' || ? || ' hours')
        GROUP BY ih.entity_type, ih.entity_id, e.name
        ORDER BY improvement_count DESC
        LIMIT 10
        """,
        hours
    )
    
    # Get daily trends
    daily_trends = await db.fetch_all(
        """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as improvements_created,
            SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed,
            AVG(effectiveness) as avg_effectiveness
        FROM improvement_history
        WHERE created_at > datetime('now', '-' || ? || ' hours')
        GROUP BY DATE(created_at)
        ORDER BY date
        """,
        hours
    )
    
    return {
        "by_type": [dict(row) for row in by_type],
        "by_entity": [dict(row) for row in by_entity],
        "daily_trends": [dict(row) for row in daily_trends],
        "period_hours": hours
    }


@router.get("/opportunities")
async def get_optimization_opportunities(
    status: str = "pending",
    impact: Optional[str] = None,
    limit: int = 20,
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get optimization opportunities."""
    query = """
        SELECT 
            oo.*,
            e.name as entity_name
        FROM optimization_opportunities oo
        LEFT JOIN entities e ON oo.entity_type = e.entity_type AND oo.entity_id = e.entity_id
        WHERE oo.status = ?
    """
    params = [status]
    
    if impact:
        query += " AND oo.potential_impact = ?"
        params.append(impact)
    
    query += " ORDER BY oo.confidence_score DESC, oo.created_at DESC LIMIT ?"
    params.append(limit)
    
    opportunities = await db.fetch_all(query, *params)
    
    return {
        "opportunities": [_format_opportunity(opp) for opp in opportunities],
        "count": len(opportunities)
    }


@router.get("/effectiveness/{entity_type}/{entity_id}")
async def get_entity_effectiveness(
    entity_type: str,
    entity_id: int,
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get effectiveness metrics for a specific entity."""
    # Get improvement summary
    summary = await db.fetch_one(
        """
        SELECT 
            COUNT(*) as total_improvements,
            SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'rolled_back' THEN 1 ELSE 0 END) as rolled_back,
            AVG(effectiveness) as avg_effectiveness,
            MAX(effectiveness) as best_improvement,
            MIN(effectiveness) as worst_improvement
        FROM improvement_history
        WHERE entity_type = ? AND entity_id = ?
        """,
        entity_type, entity_id
    )
    
    # Get recent improvements
    recent = await db.fetch_all(
        """
        SELECT 
            improvement_id,
            improvement_type,
            description,
            status,
            effectiveness,
            created_at
        FROM improvement_history
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        entity_type, entity_id
    )
    
    # Get before/after metrics comparison
    comparisons = await db.fetch_all(
        """
        SELECT 
            improvement_id,
            metrics_before,
            metrics_after,
            effectiveness
        FROM improvement_history
        WHERE entity_type = ? 
          AND entity_id = ?
          AND status = 'deployed'
          AND metrics_before IS NOT NULL
          AND metrics_after IS NOT NULL
        ORDER BY effectiveness DESC
        LIMIT 5
        """,
        entity_type, entity_id
    )
    
    return {
        "entity": f"{entity_type}_{entity_id}",
        "summary": dict(summary) if summary else {},
        "recent_improvements": [dict(row) for row in recent],
        "metric_comparisons": [_format_comparison(comp) for comp in comparisons]
    }


@router.get("/review-queue")
async def get_review_queue(
    db: DatabaseManager = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get entities pending review."""
    reviews = await db.fetch_all(
        """
        SELECT 
            rrc.*,
            e.name as entity_name,
            e.state,
            (
                SELECT COUNT(*) 
                FROM tasks 
                WHERE agent_id = e.entity_id 
                  AND created_at > rrc.last_review_date
            ) as tasks_since_review,
            (
                SELECT AVG(CAST(metadata->>'$.duration' AS REAL))
                FROM events
                WHERE entity_type = e.entity_type 
                  AND entity_id = e.entity_id
                  AND event_type = 'TASK_COMPLETED'
                  AND created_at > datetime('now', '-7 days')
            ) as recent_avg_duration
        FROM rolling_review_counters rrc
        JOIN entities e ON rrc.entity_id = e.entity_id AND rrc.entity_type = e.entity_type
        WHERE e.state = 'active'
          AND (
            (rrc.review_trigger_type = 'threshold' AND rrc.task_count >= rrc.review_interval)
            OR
            (rrc.review_trigger_type = 'periodic' 
             AND datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now'))
            OR
            (rrc.review_trigger_type = 'hybrid' 
             AND (rrc.task_count >= rrc.review_interval 
                  OR datetime(rrc.last_review_date, '+' || rrc.review_interval || ' days') <= datetime('now')))
          )
        ORDER BY rrc.task_count DESC
        """
    )
    
    return {
        "pending_reviews": [_format_review(review) for review in reviews],
        "count": len(reviews)
    }


@router.post("/trigger-improvement/{entity_type}/{entity_id}")
async def trigger_improvement(
    entity_type: str,
    entity_id: int,
    improvement_type: str,
    description: str,
    engine: SelfImprovementEngine = Depends(get_improvement_engine),
    current_user: Dict = Depends(get_current_user)
):
    """Manually trigger an improvement for an entity."""
    # Create manual improvement
    from ..core.self_improvement_engine import Improvement, ImprovementType, ImprovementStatus
    
    try:
        imp_type = ImprovementType(improvement_type)
    except ValueError:
        raise HTTPException(400, f"Invalid improvement type: {improvement_type}")
    
    improvement = Improvement(
        improvement_id=f"manual_{entity_type}_{entity_id}_{datetime.utcnow().timestamp()}",
        improvement_type=imp_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        rationale="Manually triggered by user",
        expected_impact={"manual": True},
        changes={},
        status=ImprovementStatus.PROPOSED,
        created_at=datetime.utcnow()
    )
    
    # Add to queue
    engine.improvement_queue.append(improvement)
    
    return {
        "improvement_id": improvement.improvement_id,
        "status": "queued",
        "queue_position": len(engine.improvement_queue)
    }


@router.get("/config")
async def get_improvement_config(
    engine: SelfImprovementEngine = Depends(get_improvement_engine),
    current_user: Dict = Depends(get_current_user)
):
    """Get self-improvement engine configuration."""
    return {
        "min_confidence_score": engine.min_confidence_score,
        "test_duration_hours": engine.test_duration_hours,
        "improvement_batch_size": engine.improvement_batch_size,
        "rollback_threshold": engine.rollback_threshold,
        "max_concurrent_improvements": engine.max_concurrent_improvements,
        "cooldown_period_hours": engine.cooldown_period.total_seconds() / 3600
    }


@router.put("/config")
async def update_improvement_config(
    config_updates: Dict[str, Any],
    engine: SelfImprovementEngine = Depends(get_improvement_engine),
    current_user: Dict = Depends(get_current_user)
):
    """Update self-improvement engine configuration."""
    # Validate and apply updates
    if "min_confidence_score" in config_updates:
        engine.min_confidence_score = float(config_updates["min_confidence_score"])
    
    if "test_duration_hours" in config_updates:
        engine.test_duration_hours = int(config_updates["test_duration_hours"])
    
    if "improvement_batch_size" in config_updates:
        engine.improvement_batch_size = int(config_updates["improvement_batch_size"])
    
    if "rollback_threshold" in config_updates:
        engine.rollback_threshold = float(config_updates["rollback_threshold"])
    
    if "max_concurrent_improvements" in config_updates:
        engine.max_concurrent_improvements = int(config_updates["max_concurrent_improvements"])
    
    if "cooldown_period_hours" in config_updates:
        hours = float(config_updates["cooldown_period_hours"])
        engine.cooldown_period = timedelta(hours=hours)
    
    return {"status": "updated", "config": await get_improvement_config(engine, current_user)}


# Helper functions

def _calculate_system_health(metrics: Dict, opportunities: Dict) -> Dict[str, Any]:
    """Calculate overall system health score."""
    if not metrics:
        return {"score": 0, "status": "unknown"}
    
    # Calculate health score based on various factors
    score = 100
    
    # Penalize for low effectiveness
    if metrics.get('avg_effectiveness', 0) < 0:
        score -= 20
    
    # Penalize for high rollback rate
    total = metrics.get('total_improvements', 1)
    rollback_rate = metrics.get('rolled_back', 0) / total if total > 0 else 0
    if rollback_rate > 0.2:
        score -= 30
    elif rollback_rate > 0.1:
        score -= 15
    
    # Boost for high success rate
    success_rate = metrics.get('deployed', 0) / total if total > 0 else 0
    if success_rate > 0.8:
        score += 10
    
    # Consider pending opportunities
    if opportunities:
        high_impact = opportunities.get('high_impact', 0)
        if high_impact > 10:
            score -= 10  # Many unaddressed high-impact opportunities
    
    # Determine status
    if score >= 90:
        status = "excellent"
    elif score >= 70:
        status = "good"
    elif score >= 50:
        status = "fair"
    else:
        status = "needs_attention"
    
    return {
        "score": max(0, min(100, score)),
        "status": status,
        "factors": {
            "effectiveness": metrics.get('avg_effectiveness', 0),
            "rollback_rate": rollback_rate,
            "success_rate": success_rate
        }
    }


def _format_improvement(imp: Dict) -> Dict[str, Any]:
    """Format improvement record for API response."""
    return {
        "improvement_id": imp['improvement_id'],
        "type": imp['improvement_type'],
        "entity": f"{imp['entity_type']}_{imp['entity_id']}",
        "entity_name": imp.get('entity_name'),
        "description": imp['description'],
        "status": imp['status'],
        "effectiveness": imp.get('effectiveness'),
        "created_at": imp['created_at'],
        "deployed_at": imp.get('deployed_at'),
        "evaluated_at": imp.get('evaluated_at')
    }


def _format_opportunity(opp: Dict) -> Dict[str, Any]:
    """Format optimization opportunity for API response."""
    return {
        "id": opp['id'],
        "entity": f"{opp['entity_type']}_{opp['entity_id']}",
        "entity_name": opp.get('entity_name'),
        "type": opp['opportunity_type'],
        "description": opp['description'],
        "impact": opp['potential_impact'],
        "confidence": opp['confidence_score'],
        "status": opp['status'],
        "created_at": opp['created_at'],
        "metadata": json.loads(opp.get('metadata', '{}'))
    }


def _format_review(review: Dict) -> Dict[str, Any]:
    """Format review record for API response."""
    return {
        "entity": f"{review['entity_type']}_{review['entity_id']}",
        "entity_name": review['entity_name'],
        "trigger_type": review['review_trigger_type'],
        "task_count": review['task_count'],
        "review_interval": review['review_interval'],
        "last_review": review.get('last_review_date'),
        "tasks_since_review": review.get('tasks_since_review', 0),
        "recent_performance": review.get('recent_avg_duration')
    }


def _format_comparison(comp: Dict) -> Dict[str, Any]:
    """Format metric comparison for API response."""
    before = json.loads(comp['metrics_before']) if comp['metrics_before'] else {}
    after = json.loads(comp['metrics_after']) if comp['metrics_after'] else {}
    
    improvements = []
    if before.get('error_rate', 0) > after.get('error_rate', 0):
        improvements.append({
            "metric": "error_rate",
            "before": before['error_rate'],
            "after": after['error_rate'],
            "improvement": f"{(before['error_rate'] - after['error_rate']) * 100:.1f}% reduction"
        })
    
    if before.get('avg_duration', 0) > after.get('avg_duration', 0):
        improvements.append({
            "metric": "avg_duration",
            "before": before['avg_duration'],
            "after": after['avg_duration'],
            "improvement": f"{(before['avg_duration'] - after['avg_duration']):.1f}s faster"
        })
    
    return {
        "improvement_id": comp['improvement_id'],
        "effectiveness": comp['effectiveness'],
        "improvements": improvements
    }