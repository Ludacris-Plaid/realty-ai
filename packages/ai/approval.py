"""
RealtyAI — Human Approval Workflow.

AI generates → Human approves → Executes.

Critical actions (sending emails, signing docs, spending money)
require human approval before execution.

Approval states:
  - pending: Awaiting human review
  - approved: Human approved, ready to execute
  - rejected: Human rejected
  - executed: Action was carried out
"""
import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

# In-memory fallback (used when DB is unavailable)
_pending_approvals: list[dict] = []

# DB module — lazy import
_db = None

def _get_db():
    global _db
    if _db is None:
        try:
            from db import (
                create_approval_in_db, get_pending_approvals_from_db,
                approve_in_db, reject_in_db, get_approval_history_from_db,
            )
            _db = {
                "create": create_approval_in_db,
                "pending": get_pending_approvals_from_db,
                "approve": approve_in_db,
                "reject": reject_in_db,
                "history": get_approval_history_from_db,
            }
        except Exception:
            pass
    return _db


def request_approval(
    action_type: str,
    summary: str,
    details: dict,
    agent_name: str = "General Assistant",
    requires_human: bool = True,
) -> str:
    """Create an approval request. Persists to PostgreSQL, falls back to in-memory.
    
    Args:
        action_type: e.g. 'send_email', 'create_campaign', 'schedule_showing'
        summary: One-line summary for the approval UI
        details: Full context for the human to review
        agent_name: Which agent created this
        requires_human: If False, auto-approves (for low-risk actions)
    
    Returns:
        Approval request ID.
    """
    db = _get_db()
    if db:
        try:
            return db["create"](action_type, summary, details, agent_name, requires_human)
        except Exception as e:
            logger.warning(f"DB approval create failed, using in-memory: {e}")

    approval_id = str(uuid.uuid4())
    entry = {
        "id": approval_id,
        "action_type": action_type,
        "summary": summary,
        "details": details,
        "agent_name": agent_name,
        "status": "approved" if not requires_human else "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewed_by": None,
        "notes": None,
    }
    _pending_approvals.insert(0, entry)
    return approval_id


def approve(approval_id: str, reviewer: str = "Agent", notes: Optional[str] = None) -> Optional[dict]:
    """Approve a pending action. Returns the entry or None if not found."""
    db = _get_db()
    if db:
        try:
            return db["approve"](approval_id, reviewer, notes)
        except Exception as e:
            logger.warning(f"DB approve failed, using in-memory: {e}")
    
    for entry in _pending_approvals:
        if entry["id"] == approval_id and entry["status"] == "pending":
            entry["status"] = "approved"
            entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            entry["reviewed_by"] = reviewer
            entry["notes"] = notes
            return entry
    return None


def reject(approval_id: str, reviewer: str = "Agent", reason: Optional[str] = None) -> Optional[dict]:
    """Reject a pending action. Returns the entry or None if not found."""
    db = _get_db()
    if db:
        try:
            return db["reject"](approval_id, reviewer, reason)
        except Exception as e:
            logger.warning(f"DB reject failed, using in-memory: {e}")
    
    for entry in _pending_approvals:
        if entry["id"] == approval_id and entry["status"] == "pending":
            entry["status"] = "rejected"
            entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            entry["reviewed_by"] = reviewer
            entry["notes"] = reason
            return entry
    return None


def get_pending_approvals() -> list[dict]:
    """Return all actions awaiting human approval from PostgreSQL (fallback to in-memory)."""
    db = _get_db()
    if db:
        try:
            return db["pending"]()
        except Exception as e:
            logger.warning(f"DB pending approvals failed, using in-memory: {e}")
    return [a for a in _pending_approvals if a["status"] == "pending"]


def get_approval_history(limit: int = 20) -> list[dict]:
    """Return recent approval decisions from PostgreSQL (fallback to in-memory)."""
    db = _get_db()
    if db:
        try:
            return db["history"](limit=limit)
        except Exception as e:
            logger.warning(f"DB approval history failed, using in-memory: {e}")
    return _pending_approvals[:limit]


def execute_action(approval_id: str) -> Optional[dict]:
    """Mark an approved action as executed."""
    # Note: DB-backed execute_action can be added when needed
    for entry in _pending_approvals:
        if entry["id"] == approval_id and entry["status"] == "approved":
            entry["status"] = "executed"
            return entry
    return None
