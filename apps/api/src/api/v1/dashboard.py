from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import engine

router = APIRouter()


@router.get("/summary")
def dashboard_summary():
    with Session(engine) as session:
        lead_stats = session.execute(text("""
            SELECT
                COUNT(*)::int AS total_leads,
                COUNT(*) FILTER (WHERE ai_score >= 80)::int AS hot_leads_count
            FROM leads
        """)).fetchone()

        leads_by_status_rows = session.execute(text("""
            SELECT status, COUNT(*)::int AS cnt
            FROM leads
            GROUP BY status
            ORDER BY cnt DESC
        """)).fetchall()

        listing_stats = session.execute(text("""
            SELECT
                COUNT(*)::int AS total_leads,
                COUNT(*) FILTER (WHERE status = 'ACTIVE')::int AS active_listings,
                COALESCE(SUM(list_price), 0)::numeric(14,2) AS total_value
            FROM properties
        """)).fetchone()

        try:
            recent = session.execute(text("""
                SELECT id, agent_name, action, intent, model_used, status,
                       (created_at AT TIME ZONE 'UTC')::text AS created_at
                FROM activities
                ORDER BY created_at DESC
                LIMIT 10
            """)).fetchall()
        except Exception:
            recent = []

        try:
            approvals = session.execute(text("""
                SELECT COUNT(*)::int AS cnt
                FROM approvals
                WHERE status = 'pending'
            """)).scalar()
        except Exception:
            approvals = 0

    return {
        "total_leads": lead_stats[0] or 0,
        "hot_leads_count": lead_stats[1] or 0,
        "leads_by_status": {r[0]: r[1] for r in leads_by_status_rows},
        "total_listings": listing_stats[0] or 0,
        "active_listings": listing_stats[1] or 0,
        "total_value": float(listing_stats[2] or 0),
        "recent_activities": [
            {
                "id": str(r[0]),
                "agent_name": r[1],
                "action": r[2],
                "intent": r[3],
                "model_used": r[4],
                "status": r[5],
                "created_at": r[6],
            }
            for r in recent
        ],
        "pending_approvals": approvals or 0,
        "today_showings": 0,
    }
