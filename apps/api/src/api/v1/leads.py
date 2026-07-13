import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import engine

router = APIRouter()

DEFAULT_AGENT_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
DEFAULT_ORG_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: str = "other"
    status: str = "new"
    budget: Optional[float] = None
    location_interest: Optional[str] = None
    property_type_interest: Optional[str] = None
    timeline: Optional[str] = None
    pre_approved: Optional[bool] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    location_interest: Optional[str] = None
    property_type_interest: Optional[str] = None
    timeline: Optional[str] = None
    pre_approved: Optional[bool] = None
    last_contacted_at: Optional[datetime] = None
    notes: Optional[str] = None


def _row_to_dict(r):
    return {
        "id": str(r[0]),
        "agent_id": str(r[1]) if r[1] else None,
        "first_name": r[2],
        "last_name": r[3],
        "email": r[4],
        "phone": r[5],
        "source": r[6],
        "status": r[7],
        "budget": float(r[8]) if r[8] is not None else None,
        "location_interest": r[9],
        "property_type_interest": r[10],
        "timeline": r[11],
        "pre_approved": r[12],
        "ai_score": r[13] or 0,
        "ai_score_reason": r[14] or "",
        "ai_score_updated_at": r[15].isoformat() if r[15] else None,
        "last_contacted_at": r[16].isoformat() if r[16] else None,
        "notes": r[17] or "",
        "created_at": r[18].isoformat() if r[18] else None,
        "updated_at": r[19].isoformat() if r[19] else None,
    }


_COLUMNS = """
    id, agent_id, first_name, last_name, email, phone, source, status,
    budget, location_interest, property_type_interest, timeline,
    pre_approved, ai_score, ai_score_reason, ai_score_updated_at,
    last_contacted_at, notes, created_at, updated_at
"""


@router.get("/stats")
def lead_pipeline_stats():
    with Session(engine) as session:
        by_status = session.execute(
            text("SELECT status, COUNT(*)::int AS cnt FROM leads GROUP BY status ORDER BY cnt DESC")
        ).fetchall()

        total = session.execute(
            text("SELECT COUNT(*)::int FROM leads")
        ).scalar()

        avg_score = session.execute(
            text("SELECT COALESCE(AVG(ai_score), 0)::float FROM leads WHERE ai_score IS NOT NULL")
        ).scalar()

        source_breakdown = session.execute(
            text("SELECT source, COUNT(*)::int AS cnt FROM leads GROUP BY source ORDER BY cnt DESC")
        ).fetchall()

    return {
        "total": total or 0,
        "by_status": {r[0]: r[1] for r in by_status},
        "avg_ai_score": round(avg_score, 1) if avg_score else 0,
        "by_source": {r[0]: r[1] for r in source_breakdown},
    }


@router.get("/")
def list_leads(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    query = f"SELECT {_COLUMNS} FROM leads WHERE 1=1"
    params = {}
    if status:
        query += " AND status = :status"
        params["status"] = status
    if source:
        query += " AND source = :source"
        params["source"] = source
    if search:
        query += " AND (LOWER(first_name) LIKE :search OR LOWER(last_name) LIKE :search OR LOWER(email) LIKE :search)"
        params["search"] = f"%{search.lower()}%"
    query += " ORDER BY ai_score DESC NULLS LAST, created_at DESC"

    with Session(engine) as session:
        rows = session.execute(text(query), params).fetchall()

    return {"leads": [_row_to_dict(r) for r in rows], "total": len(rows)}


@router.get("/{lead_id}")
def get_lead(lead_id: str):
    with Session(engine) as session:
        row = session.execute(
            text(f"SELECT {_COLUMNS} FROM leads WHERE id = :id"),
            {"id": lead_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _row_to_dict(row)


@router.post("/", status_code=201)
def create_lead(data: LeadCreate):
    lead_id = str(uuid.uuid4())
    now = datetime.utcnow()

    with Session(engine) as session:
        session.execute(
            text("""
                INSERT INTO leads
                    (id, agent_id, brokerage_id,
                     first_name, last_name, email, phone,
                     source, status, budget, location_interest,
                     property_type_interest, timeline, pre_approved, notes,
                     created_at, updated_at)
                VALUES
                    (:id, :agent_id, :brokerage_id,
                     :first_name, :last_name, :email, :phone,
                     :source, :status, :budget, :location_interest,
                     :property_type_interest, :timeline, :pre_approved, :notes,
                     :created_at, :updated_at)
            """),
            {
                "id": lead_id,
                "agent_id": DEFAULT_AGENT_ID,
                "brokerage_id": DEFAULT_ORG_ID,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "email": data.email,
                "phone": data.phone,
                "source": data.source,
                "status": data.status,
                "budget": data.budget,
                "location_interest": data.location_interest,
                "property_type_interest": data.property_type_interest,
                "timeline": data.timeline,
                "pre_approved": data.pre_approved,
                "notes": data.notes,
                "created_at": now,
                "updated_at": now,
            },
        )
        session.commit()

    return get_lead(lead_id)


@router.put("/{lead_id}")
def update_lead(lead_id: str, data: LeadUpdate):
    fields = data.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    field_map = {
        "first_name": "first_name", "last_name": "last_name",
        "email": "email", "phone": "phone",
        "source": "source", "status": "status",
        "budget": "budget", "location_interest": "location_interest",
        "property_type_interest": "property_type_interest",
        "timeline": "timeline", "pre_approved": "pre_approved",
        "last_contacted_at": "last_contacted_at", "notes": "notes",
    }

    set_parts = []
    params = {"id": lead_id}
    for py_field, db_col in field_map.items():
        if py_field in fields:
            set_parts.append(f"{db_col} = :{py_field}")
            params[py_field] = fields[py_field]

    set_parts.append("updated_at = NOW()")

    with Session(engine) as session:
        result = session.execute(
            text(f"UPDATE leads SET {', '.join(set_parts)} WHERE id = :id"),
            params,
        )
        session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Lead not found")

    return get_lead(lead_id)


@router.delete("/{lead_id}")
def delete_lead(lead_id: str):
    with Session(engine) as session:
        result = session.execute(
            text("DELETE FROM leads WHERE id = :id"),
            {"id": lead_id},
        )
        session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "deleted", "id": lead_id}


class ScoreResponse(BaseModel):
    id: str
    ai_score: float
    ai_score_reason: str


@router.patch("/{lead_id}/score")
def rescore_lead(lead_id: str):
    with Session(engine) as session:
        row = session.execute(
            text("""
                SELECT id, first_name, last_name, email, phone, source, status,
                       budget, location_interest, property_type_interest, timeline,
                       pre_approved, notes
                FROM leads WHERE id = :id
            """),
            {"id": lead_id},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_data = {
        "first_name": row[1], "last_name": row[2],
        "email": row[3], "phone": row[4],
        "source": row[5], "status": row[6],
        "budget": float(row[7]) if row[7] else None,
        "location_interest": row[8],
        "property_type_interest": row[9],
        "timeline": row[10],
        "pre_approved": row[11],
        "notes": row[12] or "",
    }

    score = 50
    reason_parts = []

    if lead_data["pre_approved"]:
        score += 20
        reason_parts.append("Pre-approved")
    if lead_data["timeline"] in ("immediate", "30_days"):
        score += 15
        reason_parts.append(f"Timeline: {lead_data['timeline']}")
    if lead_data["budget"] and lead_data["budget"] > 500000:
        score += 10
        reason_parts.append(f"Strong budget (${lead_data['budget']:,.0f})")
    if lead_data["status"] in ("qualified", "appointment_set"):
        score += 10
        reason_parts.append(f"Status: {lead_data['status']}")
    if lead_data["source"] in ("referral",):
        score += 5
        reason_parts.append("Referral source")

    score = min(score, 99)
    reason = ". ".join(reason_parts) if reason_parts else "Standard scoring"

    with Session(engine) as session:
        session.execute(
            text("""
                UPDATE leads
                SET ai_score = :score, ai_score_reason = :reason, ai_score_updated_at = NOW()
                WHERE id = :id
            """),
            {"id": lead_id, "score": score, "reason": reason},
        )
        session.commit()

    return ScoreResponse(id=lead_id, ai_score=score, ai_score_reason=reason)
