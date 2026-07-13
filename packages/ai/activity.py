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

# Default IDs until auth is implemented
_DEFAULT_ORG_ID = os.environ.get("DEFAULT_ORG_ID", "00000000-0000-0000-0000-000000000001")
_DEFAULT_USER_ID = os.environ.get("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000002")

# In-memory fallback (used only when DB is down)
_activities: list[dict] = []

# DB module — lazy import to avoid circular deps at module level
_db = None

def _get_db():
    global _db
    if _db is None:
        try:
            from db import record_activity_in_db, get_recent_activities_from_db
            _db = {"record": record_activity_in_db, "list": get_recent_activities_from_db}
        except Exception:
            pass
    return _db


def record_activity(
    agent_name: str,
    action: str,
    intent: str = "general",
    model_used: str = "fast-model",
    status: str = "success",
    metadata: Optional[dict] = None,
) -> str:
    """Record an AI activity entry. Persists to PostgreSQL, falls back to in-memory.
    
    Returns the activity ID.
    """
    db = _get_db()
    if db:
        try:
            return db["record"](
                organization_id=_DEFAULT_ORG_ID,
                user_id=_DEFAULT_USER_ID,
                agent_name=agent_name,
                action=action,
                intent=intent,
                model_used=model_used,
                status=status,
                metadata=metadata,
            )
        except Exception as e:
            logger.warning(f"DB activity record failed, using in-memory fallback: {e}")

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


def get_recent_activities(limit: int = 20) -> list[dict]:
    """Return the most recent AI activities from PostgreSQL (fallback to in-memory)."""
    db = _get_db()
    if db:
        try:
            return db["list"](limit=limit, organization_id=_DEFAULT_ORG_ID)
        except Exception as e:
            logger.warning(f"DB activity list failed, using in-memory fallback: {e}")
    return _activities[:limit]


def get_activities_by_agent(agent_name: str, limit: int = 20) -> list[dict]:
    """Return activities for a specific agent. Falls back to in-memory if DB unavailable."""
    db = _get_db()
    if db:
        try:
            all_activities = db["list"](limit=100, organization_id=_DEFAULT_ORG_ID)
            return [a for a in all_activities if a.get("agent_name") == agent_name][:limit]
        except Exception:
            pass
    return [a for a in _activities if a["agent_name"] == agent_name][:limit]


def get_activity_stats() -> dict:
    """Return aggregate stats about AI activity from PostgreSQL (fallback to in-memory)."""
    db = _get_db()
    if db:
        try:
            all_activities = db["list"](limit=500, organization_id=_DEFAULT_ORG_ID)
            if all_activities:
                by_agent = {}
                for a in all_activities:
                    name = a.get("agent_name", "unknown")
                    by_agent[name] = by_agent.get(name, 0) + 1
                return {
                    "total_actions": len(all_activities),
                    "by_agent": by_agent,
                    "last_24h": 0,  # timestamp-based filtering TBD
                }
        except Exception:
            pass

    return {"total_actions": 0, "by_agent": {}, "last_24h": 0}
