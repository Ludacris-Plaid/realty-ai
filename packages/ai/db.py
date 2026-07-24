"""
RealtyAI — Database Access Layer for AI Tools.

Provides synchronous database access for LangChain @tool functions.
Replaces the in-memory mock data with real PostgreSQL queries.
"""
import os
from typing import Optional
from datetime import datetime
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database URL for sync access (tools are synchronous)
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://realty:realty_local_dev@localhost:5433/realty_ai"
).replace("+asyncpg", "").replace("+psycopg", "")

engine = create_engine(DB_URL, echo=False)


def _get_db_engine():
    """Return the shared SQLAlchemy engine. Returns None if not available."""
    try:
        return engine
    except Exception:
        return None


# ─── Lead Queries ──────────────────────────────────────────────────────────────

def get_hot_leads_from_db(limit: int = 5) -> list[dict]:
    """Return highest-scored leads from the database."""
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT id, first_name, last_name, email, phone, source, status,
                       budget, location_interest, property_type_interest, timeline,
                       pre_approved, ai_score, ai_score_reason, notes, last_contacted_at
                FROM leads
                WHERE ai_score IS NOT NULL
                ORDER BY ai_score DESC
                LIMIT :lim
            """),
            {"lim": limit}
        ).fetchall()

    return [
        {
            "id": str(r[0]),
            "first_name": r[1], "last_name": r[2],
            "email": r[3], "phone": r[4],
            "source": r[5], "status": r[6],
            "budget": float(r[7]) if r[7] else None,
            "location_interest": r[8],
            "property_type_interest": r[9],
            "timeline": r[10],
            "pre_approved": r[11],
            "ai_score": r[12] or 0,
            "ai_score_reason": r[13] or "",
            "notes": r[14] or "",
            "last_contacted_at": r[15].isoformat() if r[15] else None,
        }
        for r in rows
    ]


def search_leads_in_db(name: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    """Search leads by name or status."""
    query = """
        SELECT id, first_name, last_name, email, phone, source, status,
               budget, location_interest, property_type_interest, timeline,
               pre_approved, ai_score, ai_score_reason, notes, last_contacted_at
        FROM leads WHERE 1=1
    """
    params = {}
    if name:
        query += " AND (LOWER(first_name) LIKE :name OR LOWER(last_name) LIKE :name)"
        params["name"] = f"%{name.lower()}%"
    if status:
        query += " AND status = :status"
        params["status"] = status

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return [
        {
            "id": str(r[0]),
            "first_name": r[1], "last_name": r[2],
            "email": r[3], "phone": r[4],
            "source": r[5], "status": r[6],
            "budget": float(r[7]) if r[7] else None,
            "location_interest": r[8],
            "property_type_interest": r[9],
            "timeline": r[10],
            "pre_approved": r[11],
            "ai_score": r[12] or 0,
            "ai_score_reason": r[13] or "",
            "notes": r[14] or "",
            "last_contacted_at": r[15].isoformat() if r[15] else None,
        }
        for r in rows
    ]


def get_lead_count_from_db() -> dict:
    """Get lead counts by status."""
    with Session(engine) as session:
        rows = session.execute(
            text("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status")
        ).fetchall()
        total = session.execute(text("SELECT COUNT(*) FROM leads")).scalar()

    by_status = {r[0]: r[1] for r in rows}
    return {"total": total, "by_status": by_status}


def get_lead_by_id(lead_id: str) -> Optional[dict]:
    """Get a single lead by ID."""
    with Session(engine) as session:
        row = session.execute(
            text("""
                SELECT id, first_name, last_name, email, phone, source, status,
                       budget, location_interest, property_type_interest, timeline,
                       pre_approved, ai_score, ai_score_reason, notes, last_contacted_at,
                       created_at, updated_at
                FROM leads WHERE id = :id
            """),
            {"id": lead_id}
        ).fetchone()

    if not row:
        return None
    return {
        "id": str(row[0]),
        "first_name": row[1], "last_name": row[2],
        "email": row[3], "phone": row[4],
        "source": row[5], "status": row[6],
        "budget": float(row[7]) if row[7] else None,
        "location_interest": row[8],
        "property_type_interest": row[9],
        "timeline": row[10],
        "pre_approved": row[11],
        "ai_score": row[12] or 0,
        "ai_score_reason": row[13] or "",
        "notes": row[14] or "",
        "last_contacted_at": row[15].isoformat() if row[15] else None,
        "created_at": row[16].isoformat() if row[16] else None,
        "updated_at": row[17].isoformat() if row[17] else None,
    }


def update_lead_score(lead_id: str, score: float, reason: str) -> bool:
    """Update a lead's AI score."""
    with Session(engine) as session:
        result = session.execute(
            text("""
                UPDATE leads SET ai_score = :score, ai_score_reason = :reason,
                    ai_score_updated_at = NOW()
                WHERE id = :id
            """),
            {"id": lead_id, "score": score, "reason": reason}
        )
        session.commit()
        return result.rowcount > 0


# ─── Property Queries ──────────────────────────────────────────────────────────

def get_active_listings_from_db() -> list[dict]:
    """Return all active property listings."""
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT id, address_street, address_city, address_state, address_zip,
                       property_type, status, beds, baths, sqft, lot_size, year_built,
                       garage_spaces, list_price, description, features, mls_number,
                       created_at
                FROM properties
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
        ).fetchall()

    return [
        {
            "id": str(r[0]),
            "address_street": r[1], "address_city": r[2],
            "address_state": r[3], "address_zip": r[4],
            "property_type": r[5], "status": r[6],
            "beds": r[7], "baths": r[8],
            "sqft": r[9], "lot_size": r[10],
            "year_built": r[11], "garage_spaces": r[12],
            "list_price": float(r[13]) if r[13] else 0,
            "description": r[14] or "",
            "features": r[15] or [],
            "mls_number": r[16] or "",
        }
        for r in rows
    ]


def search_properties_in_db(city: Optional[str] = None, min_price: Optional[float] = None,
                            max_price: Optional[float] = None, beds: Optional[int] = None) -> list[dict]:
    """Search properties by criteria."""
    query = """
        SELECT id, address_street, address_city, address_state, address_zip,
               property_type, status, beds, baths, sqft, list_price, description,
               features, mls_number
        FROM properties WHERE status = 'active'
    """
    params = {}
    if city:
        query += " AND LOWER(address_city) LIKE :city"
        params["city"] = f"%{city.lower()}%"
    if min_price:
        query += " AND list_price >= :min_price"
        params["min_price"] = min_price
    if max_price:
        query += " AND list_price <= :max_price"
        params["max_price"] = max_price
    if beds:
        query += " AND beds >= :beds"
        params["beds"] = beds

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return [
        {
            "id": str(r[0]),
            "address_street": r[1], "address_city": r[2],
            "address_state": r[3], "address_zip": r[4],
            "property_type": r[5], "status": r[6],
            "beds": r[7], "baths": r[8],
            "sqft": r[9],
            "list_price": float(r[10]) if r[10] else 0,
            "description": r[11] or "",
            "features": r[12] or [],
            "mls_number": r[13] or "",
        }
        for r in rows
    ]


# ─── Activity Queries ──────────────────────────────────────────────────────────

def record_activity_in_db(organization_id: str, user_id: str, agent_name: str,
                          action: str, intent: str = "general",
                          model_used: str = "fast-model", status: str = "success",
                          metadata: Optional[dict] = None) -> str:
    """Record an activity entry in the database."""
    activity_id = str(uuid.uuid4())
    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO activities (id, organization_id, user_id, agent_name, action,
                                       intent, model_used, status, metadata)
                VALUES (:id, :org_id, :user_id, :agent_name, :action,
                        :intent, :model_used, :status, :metadata)
            """),
            {
                "id": activity_id,
                "org_id": organization_id,
                "user_id": user_id,
                "agent_name": agent_name,
                "action": action,
                "intent": intent,
                "model_used": model_used,
                "status": status,
                "metadata": metadata or {},
            }
        )
        session.commit()
    return activity_id


def get_recent_activities_from_db(limit: int = 20, organization_id: Optional[str] = None) -> list[dict]:
    """Return recent activities."""
    query = """
        SELECT id, agent_name, action, intent, model_used, status, created_at
        FROM activities
    """
    params = {}
    if organization_id:
        query += " WHERE organization_id = :org_id"
        params["org_id"] = organization_id
    query += " ORDER BY created_at DESC LIMIT :lim"
    params["lim"] = limit

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return [
        {
            "id": str(r[0]),
            "agent_name": r[1],
            "action": r[2],
            "intent": r[3],
            "model_used": r[4],
            "status": r[5],
            "created_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


# ─── Approval Queries ──────────────────────────────────────────────────────────

def create_approval_in_db(action_type: str, summary: str, details: dict,
                           agent_name: str = "General Assistant",
                           requires_human: bool = True) -> str:
    """Create an approval request in the database."""
    approval_id = str(uuid.uuid4())
    status = "pending" if requires_human else "approved"
    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO approvals (id, action_type, summary, details, agent_name, status)
                VALUES (:id, :action_type, :summary, :details, :agent_name, :status)
            """),
            {
                "id": approval_id,
                "action_type": action_type,
                "summary": summary,
                "details": details,
                "agent_name": agent_name,
                "status": status,
            }
        )
        session.commit()
    return approval_id


def get_pending_approvals_from_db(limit: int = 50) -> list[dict]:
    """Return all pending approval requests."""
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT id, action_type, summary, details, agent_name, status, created_at
                FROM approvals WHERE status = 'pending'
                ORDER BY created_at DESC LIMIT :lim
            """),
            {"lim": limit}
        ).fetchall()

    return [
        {
            "id": str(r[0]),
            "action_type": r[1],
            "summary": r[2],
            "details": r[3] if isinstance(r[3], dict) else {},
            "agent_name": r[4],
            "status": r[5],
            "created_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


def approve_in_db(approval_id: str, reviewer: str = "Agent", notes: str = None) -> Optional[dict]:
    """Approve a pending action. Returns the entry or None if not found/already reviewed."""
    with Session(engine) as session:
        result = session.execute(
            text("""
                UPDATE approvals SET status = 'approved',
                    reviewed_at = NOW(), reviewed_by = :reviewer, notes = :notes
                WHERE id = :id AND status = 'pending'
                RETURNING id, action_type, summary, status, reviewed_by
            """),
            {"id": approval_id, "reviewer": reviewer, "notes": notes}
        ).fetchone()
        session.commit()
        if not result:
            return None
        return {
            "id": str(result[0]),
            "action_type": result[1],
            "summary": result[2],
            "status": result[3],
            "reviewed_by": result[4],
        }


def reject_in_db(approval_id: str, reviewer: str = "Agent", reason: str = None) -> Optional[dict]:
    """Reject a pending action. Returns the entry or None."""
    with Session(engine) as session:
        result = session.execute(
            text("""
                UPDATE approvals SET status = 'rejected',
                    reviewed_at = NOW(), reviewed_by = :reviewer, notes = :reason
                WHERE id = :id AND status = 'pending'
                RETURNING id, action_type, summary, status, reviewed_by
            """),
            {"id": approval_id, "reviewer": reviewer, "reason": reason}
        ).fetchone()
        session.commit()
        if not result:
            return None
        return {
            "id": str(result[0]),
            "action_type": result[1],
            "summary": result[2],
            "status": result[3],
            "reviewed_by": result[4],
        }


def get_approval_history_from_db(limit: int = 20) -> list[dict]:
    """Return recent approval decisions."""
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT id, action_type, summary, agent_name, status, created_at, reviewed_at, reviewed_by
                FROM approvals WHERE status != 'pending'
                ORDER BY reviewed_at DESC LIMIT :lim
            """),
            {"lim": limit}
        ).fetchall()

    return [
        {
            "id": str(r[0]),
            "action_type": r[1],
            "summary": r[2],
            "agent_name": r[3],
            "status": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "reviewed_at": r[6].isoformat() if r[6] else None,
            "reviewed_by": r[7],
        }
        for r in rows
    ]
