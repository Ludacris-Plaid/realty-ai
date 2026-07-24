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


def _try_db(call_name: str, *args, **kwargs) -> tuple[bool, any]:
    """Try a DB operation. Returns (success, result).
    
    Each attempt re-imports the db module so transient failures
    (e.g. DB restart) don't permanently disable DB mode.
    """
    try:
        if call_name == "create":
            from db import create_approval_in_db
            result = create_approval_in_db(*args, **kwargs)
        elif call_name == "pending":
            from db import get_pending_approvals_from_db
            result = get_pending_approvals_from_db(*args, **kwargs)
        elif call_name == "approve":
            from db import approve_in_db
            result = approve_in_db(*args, **kwargs)
        elif call_name == "reject":
            from db import reject_in_db
            result = reject_in_db(*args, **kwargs)
        elif call_name == "history":
            from db import get_approval_history_from_db
            result = get_approval_history_from_db(*args, **kwargs)
        else:
            return False, None
        return True, result
    except Exception as e:
        logger.warning(f"DB approval {call_name} failed: {e}")
        return False, None


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
    ok, result = _try_db("create", action_type, summary, details, agent_name, requires_human)
    if ok:
        return result

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
    ok, result = _try_db("approve", approval_id, reviewer, notes)
    if ok:
        return result
    
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
    ok, result = _try_db("reject", approval_id, reviewer, reason)
    if ok:
        return result
    
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
    ok, result = _try_db("pending")
    if ok:
        return result
    return [a for a in _pending_approvals if a["status"] == "pending"]


def get_approval_history(limit: int = 20) -> list[dict]:
    """Return recent approval decisions from PostgreSQL (fallback to in-memory)."""
    ok, result = _try_db("history", limit=limit)
    if ok:
        return result
    return _pending_approvals[:limit]


def execute_action(approval_id: str) -> Optional[dict]:
    """Mark an approved action as executed."""
    for entry in _pending_approvals:
        if entry["id"] == approval_id and entry["status"] == "approved":
            entry["status"] = "executed"
            return entry
    return None
