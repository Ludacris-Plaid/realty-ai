"""
RealtyAI — AI Activity Feed.

Tracks every action the AI takes so the agent can see what happened.
Persisted to PostgreSQL (via db.py), falls back to in-memory if DB unavailable.

Each activity entry:
  - timestamp
  - agent_name (which specialist handled it)
  - action description
  - intent classified
  - model_used
  - status (success, pending_approval, rejected, error)
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

# In-memory fallback (used only when DB is down)
_activities: list[dict] = []


def _record_in_db(organization_id: str, user_id: str, agent_name: str,
                  action: str, intent: str = "general",
                  model_used: str = "fast-model", status: str = "success",
                  metadata: Optional[dict] = None) -> Optional[str]:
    """Try to record activity in PostgreSQL. Returns activity_id or None."""
    try:
        from db import record_activity_in_db
        return record_activity_in_db(
            organization_id=organization_id,
            user_id=user_id,
            agent_name=agent_name,
            action=action,
            intent=intent,
            model_used=model_used,
            status=status,
            metadata=metadata,
        )
    except Exception as e:
        logger.warning(f"DB activity record failed: {e}")
        return None


def record_activity(
    agent_name: str,
    action: str,
    intent: str = "general",
    model_used: str = "fast-model",
    status: str = "success",
    metadata: Optional[dict] = None,
    organization_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Record an AI activity entry. Persists to PostgreSQL, falls back to in-memory.
    
    Returns the activity ID.
    """
    # Try DB first
    if organization_id and user_id:
        result = _record_in_db(
            organization_id=organization_id,
            user_id=user_id,
            agent_name=agent_name,
            action=action,
            intent=intent,
            model_used=model_used,
            status=status,
            metadata=metadata,
        )
        if result:
            return result

    # Fallback: in-memory
    activity_id = str(uuid.uuid4())
    entry = {
        "id": activity_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "action": action,
        "intent": intent,
        "model_used": model_used,
        "status": status,
        "metadata": metadata or {},
    }
    _activities.insert(0, entry)
    if len(_activities) > 500:
        _activities.pop()
    return activity_id


def _list_from_db(limit: int = 20, organization_id: Optional[str] = None) -> Optional[list[dict]]:
    """Try to list activities from PostgreSQL. Returns list or None."""
    try:
        from db import get_recent_activities_from_db
        return get_recent_activities_from_db(limit=limit, organization_id=organization_id)
    except Exception as e:
        logger.warning(f"DB activity list failed: {e}")
        return None


def get_recent_activities(limit: int = 20, organization_id: Optional[str] = None) -> list[dict]:
    """Return the most recent AI activities from PostgreSQL (fallback to in-memory)."""
    result = _list_from_db(limit=limit, organization_id=organization_id)
    if result is not None:
        return result
    return _activities[:limit]


def get_activities_by_agent(agent_name: str, limit: int = 20, organization_id: Optional[str] = None) -> list[dict]:
    """Return activities for a specific agent. Falls back to in-memory if DB unavailable."""
    result = _list_from_db(limit=100, organization_id=organization_id)
    if result is not None:
        return [a for a in result if a.get("agent_name") == agent_name][:limit]
    return [a for a in _activities if a["agent_name"] == agent_name][:limit]


def _stats_from_db(organization_id: Optional[str] = None) -> Optional[dict]:
    """Get activity stats from PostgreSQL via SQL aggregation."""
    try:
        from db import _get_db_engine
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        engine = _get_db_engine()
        if not engine:
            return None

        with Session(engine) as session:
            total = session.execute(
                text("SELECT COUNT(*)::int FROM activities")
            ).scalar() or 0

            by_agent_rows = session.execute(
                text("""
                    SELECT agent_name, COUNT(*)::int AS cnt
                    FROM activities
                    GROUP BY agent_name
                    ORDER BY cnt DESC
                """)
            ).fetchall()

            last_24h = session.execute(
                text("""
                    SELECT COUNT(*)::int FROM activities
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
            ).scalar() or 0

        return {
            "total_actions": total,
            "by_agent": {r[0]: r[1] for r in by_agent_rows},
            "last_24h": last_24h,
        }
    except Exception as e:
        logger.warning(f"DB activity stats failed: {e}")
        return None


def get_activity_stats() -> dict:
    """Return aggregate stats about AI activity from PostgreSQL (fallback to in-memory)."""
    result = _stats_from_db()
    if result is not None:
        return result
    return {"total_actions": 0, "by_agent": {}, "last_24h": 0}
