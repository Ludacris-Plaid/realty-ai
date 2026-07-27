"""Unified inbox router — clean standalone module."""
from __future__ import annotations

import os
import sys

from fastapi import APIRouter, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

router = APIRouter()


def _get_db_url():
    return os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")


@router.get("/unified")
def unified_inbox(limit: int = Query(50, le=100), platform: str = Query("")):
    db_url = _get_db_url()
    if not db_url:
        return []
    results = []
    try:
        engine = create_engine(db_url)
        with Session(engine) as session:
            rows = session.execute(
                text("SELECT id, subject, sender, sender_name, snippet, ai_classification, is_unread, received_at FROM synced_emails ORDER BY received_at DESC LIMIT :lim"),
                {"lim": limit}
            ).fetchall()
            for r in rows:
                results.append({
                    "id": str(r[0]), "title": r[1] or "(no subject)", "platform": "email",
                    "participants": [r[2] or ""], "last_message": r[4] or "",
                    "last_message_at": str(r[7]) if r[7] else "", "message_count": 1,
                    "source": "gmail", "sender_name": r[3] or r[2] or "",
                    "is_read": not r[6] if r[6] is not None else True,
                    "ai_classification": r[5],
                })
            rows2 = session.execute(
                text("SELECT id, lead_name, property_address, showing_time, status FROM showings WHERE showing_time >= NOW() ORDER BY showing_time ASC LIMIT :lim"),
                {"lim": limit}
            ).fetchall()
            for r in rows2:
                results.append({
                    "id": str(r[0]), "title": f"Showing: {r[1] or 'Client'} @ {r[2]}",
                    "platform": "calendar", "participants": [r[1] or ""],
                    "last_message": f"Status: {r[4] or 'pending'}",
                    "last_message_at": str(r[3]) if r[3] else "", "message_count": 1,
                    "source": "showing", "sender_name": r[1] or "", "is_read": True,
                })
    except Exception as e:
        print(f"UNIFIED_INBOX_ERROR: {e}", file=sys.stderr)
    results.sort(key=lambda x: x.get("last_message_at", ""), reverse=True)
    return results[:limit]


@router.get("/unified/drafts")
def unified_drafts():
    db_url = _get_db_url()
    if not db_url:
        return []
    results = []
    try:
        engine = create_engine(db_url)
        with Session(engine) as session:
            rows = session.execute(
                text("SELECT id, sender, sender_name, subject, ai_classification, ai_draft_reply, ai_suggested_action, received_at FROM synced_emails WHERE ai_draft_reply IS NOT NULL AND LENGTH(ai_draft_reply) > 2 AND ai_draft_reply != :empty ORDER BY LENGTH(ai_draft_reply) DESC LIMIT 10"),
                {"empty": "{}"}
            ).fetchall()
            for r in rows:
                body = str(r[5]) if r[5] else ""
                if body and len(body) > 3:
                    results.append({
                        "id": "ai_" + str(r[0]),
                        "to": str(r[1] or ""),
                        "subject": "Re: " + str(r[3] or ""),
                        "body": body[:500],
                        "confidence": 80, "status": "ai_generated",
                        "created_at": str(r[7]) if r[7] else "",
                        "source": "ai_auto_reply",
                        "sender_name": str(r[2] or r[1] or ""),
                        "classification": str(r[4] or ""),
                        "action": str(r[6] or ""),
                        "email_id": str(r[0]),
                    })
    except Exception as e:
        print(f"UNIFIED_DRAFTS_ERROR: {e}", file=sys.stderr)
    return results


@router.get("/unified/{thread_id}")
def unified_thread(thread_id: str):
    db_url = _get_db_url()
    if not db_url:
        return []
    try:
        engine = create_engine(db_url)
        with Session(engine) as session:
            row = session.execute(
                text("SELECT id, subject, sender, sender_name, body, snippet, received_at, ai_classification, ai_draft_reply, ai_suggested_action FROM synced_emails WHERE id = :tid"),
                {"tid": thread_id}
            ).fetchone()
            if row:
                raw = row[5] or row[4] or ""
                if raw and raw.strip().startswith("<"):
                    raw = row[5] or ""
                return [{
                    "id": str(row[0]), "role": "user", "content": raw[:5000],
                    "direction": "inbound", "platform": "email",
                    "sender": row[2] or "", "subject": row[1] or "",
                    "created_at": str(row[6]) if row[6] else "",
                    "ai_classification": row[7] or "",
                    "ai_draft_reply": row[8] or "", "ai_action": row[9] or "",
                }]
            msgs = session.execute(
                text("SELECT m.id, m.role, m.content, m.metadata, m.created_at FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE c.id = :tid ORDER BY m.created_at ASC"),
                {"tid": thread_id}
            ).fetchall()
            if msgs:
                return [{
                    "id": str(r[0]), "role": r[1], "content": r[2],
                    "direction": "inbound" if r[1] == "user" else "outbound",
                    "platform": "chat",
                    "sender": "Athena" if r[1] == "assistant" else "You",
                    "subject": "", "created_at": str(r[4]) if r[4] else "",
                } for r in msgs]
    except Exception as e:
        print(f"UNIFIED_THREAD_ERROR: {e}", file=sys.stderr)
    return []
