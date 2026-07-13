"""
RealtyAI — AI Activity Feed.

Tracks every action the AI takes so the agent can see what happened.
This visually proves the system is working and builds trust.

Each activity entry:
  - timestamp
  - agent_name (which specialist handled it)
  - action description
  - intent classified
  - model_used
  - status (success, pending_approval, rejected, error)
"""
from datetime import datetime, timezone
from typing import Optional
import uuid


# In-memory activity store. In production, replace with PostgreSQL.
_activities: list[dict] = []


def record_activity(
    agent_name: str,
    action: str,
    intent: str = "general",
    model_used: str = "fast-model",
    status: str = "success",
    metadata: Optional[dict] = None,
) -> str:
    """Record an AI activity entry.
    
    Returns the activity ID.
    """
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
    _activities.insert(0, entry)  # newest first
    # Keep last 500 activities in memory
    if len(_activities) > 500:
        _activities.pop()
    return activity_id


def get_recent_activities(limit: int = 20) -> list[dict]:
    """Return the most recent AI activities."""
    return _activities[:limit]


def get_activities_by_agent(agent_name: str, limit: int = 20) -> list[dict]:
    """Return activities for a specific agent."""
    return [a for a in _activities if a["agent_name"] == agent_name][:limit]


def get_activity_stats() -> dict:
    """Return aggregate stats about AI activity."""
    if not _activities:
        return {"total_actions": 0, "by_agent": {}, "last_24h": 0}

    by_agent = {}
    for a in _activities:
        name = a["agent_name"]
        by_agent[name] = by_agent.get(name, 0) + 1

    # Count last 24h
    cutoff = datetime.now(timezone.utc).isoformat()
    last_24h = sum(1 for a in _activities if a["timestamp"] > cutoff)

    return {
        "total_actions": len(_activities),
        "by_agent": by_agent,
        "last_24h": last_24h,
    }
