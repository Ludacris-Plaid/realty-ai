"""Identity Resolution — cross-platform contact matching.

Matches incoming contacts (email, phone) to existing leads.
Supports email -> lead, phone -> lead, and cross-platform (SMS <> email) resolution.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


def resolve_contact(
    contact: str,
    user_id: str = "",
    create_if_new: bool = False,
    first_name: str = "",
    last_name: str = "",
    source: str = "inbound",
) -> dict:
    """Resolve a contact (email OR phone) to a lead.

    Args:
        contact: Email address OR phone number
        user_id: Agent owner ID (for creating new leads)
        create_if_new: Create lead if no match found
        first_name, last_name: Used when creating new lead
        source: Source attribution (email, sms, web, etc.)

    Returns:
        dict with: lead_id, matched, was_created, confidence, details
    """
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        import os
        db_url = os.environ.get("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")
        if db_url:
            _engine = create_engine(db_url)
        else:
            return {"lead_id": None, "matched": False, "was_created": False,
                    "confidence": "no_db", "details": "No database connection"}

    contact = contact.strip().lower() if contact else ""
    if not contact:
        return {"lead_id": None, "matched": False, "was_created": False,
                "confidence": "empty", "details": "No contact provided"}

    is_email = "@" in contact
    is_phone = any(c in contact for c in "0123456789") and len(contact) >= 6

    with Session(_engine) as session:
        # Step 1: Exact match on email OR phone
        row = session.execute(
            text("SELECT id, first_name, last_name, email, phone FROM leads WHERE (LOWER(email) = :contact OR phone = :contact) LIMIT 1"),
            {"contact": contact}
        ).fetchone()

        if row:
            match_type = "email" if is_email else "phone"
            return {
                "lead_id": str(row[0]),
                "matched": True,
                "was_created": False,
                "confidence": "exact_" + match_type,
                "details": {"name": f"{row[1]} {row[2]}", "email": row[3], "phone": row[4]},
            }

        # Step 2: Partial phone match (last 10 digits)
        if is_phone:
            digits = "".join(c for c in contact if c.isdigit())
            if len(digits) >= 7:
                suffix = digits[-10:] if len(digits) >= 10 else digits
                row = session.execute(
                    text("SELECT id, first_name, last_name, email, phone FROM leads WHERE phone LIKE :suffix ORDER BY LENGTH(phone) ASC LIMIT 1"),
                    {"suffix": f"%{suffix}"}
                ).fetchone()
                if row:
                    return {
                        "lead_id": str(row[0]),
                        "matched": True,
                        "was_created": False,
                        "confidence": "partial_phone",
                        "details": {"name": f"{row[1]} {row[2]}", "email": row[3], "phone": row[4]},
                    }

        # Step 3: Email domain match
        if is_email and "@" in contact:
            domain = contact.split("@")[1]
            rows = session.execute(
                text("SELECT id, first_name, last_name, email, phone FROM leads WHERE LOWER(email) LIKE :domain LIMIT 3"),
                {"domain": f"%@{domain}"}
            ).fetchall()
            if len(rows) == 1:
                r = rows[0]
                return {
                    "lead_id": str(r[0]),
                    "matched": True,
                    "was_created": False,
                    "confidence": "domain_match",
                    "details": {"name": f"{r[1]} {r[2]}", "email": r[3], "phone": r[4]},
                }
            elif len(rows) > 1:
                return {
                    "lead_id": None,
                    "matched": False,
                    "was_created": False,
                    "confidence": "domain_ambiguous",
                    "details": {"candidates": [f"{r[1]} {r[2]} ({r[3]})" for r in rows]},
                }

        # Step 4: Create new lead if requested
        if create_if_new and user_id:
            lead_id = str(uuid.uuid4())
            if first_name and last_name:
                name = f"{first_name} {last_name}"
            elif is_email:
                name = contact.split("@")[0]
            else:
                name = contact
            fn = first_name or name.split()[0] if name.split() else name
            ln = last_name or " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

            session.execute(
                text("""INSERT INTO leads (id, agent_id, first_name, last_name, email, phone, status, source, created_at, updated_at) VALUES (:id, :uid, :fn, :ln, :email, :phone, :status, :src, NOW(), NOW())"""),
                {"id": lead_id, "uid": user_id, "fn": fn, "ln": ln,
                 "email": contact if is_email else "", "phone": contact if is_phone else "", "status": "new", "src": source}
            )
            session.commit()
            logger.info(f"Identity: Created lead {lead_id} from {contact}")
            return {
                "lead_id": lead_id, "matched": False, "was_created": True,
                "confidence": "created",
                "details": {"name": name, "email": contact if is_email else "", "phone": contact if is_phone else ""},
            }

        return {"lead_id": None, "matched": False, "was_created": False,
                "confidence": "no_match", "details": {"contact": contact}}


def link_conversation_to_lead(conversation_id: str, lead_id: str) -> bool:
    """Link a conversation to a lead by setting client_id."""
    global _engine
    if _engine is None:
        return False
    try:
        with Session(_engine) as session:
            session.execute(
                text("UPDATE conversations SET client_id = :lead_id, updated_at = NOW() WHERE id = :conv_id"),
                {"lead_id": lead_id, "conv_id": conversation_id}
            )
            session.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to link conversation {conversation_id} to lead {lead_id}: {e}")
        return False


def get_unified_contact_history(contact: str, user_id: str = "", limit: int = 20) -> dict:
    """Get all messages (email + SMS) for a contact across all platforms.

    Finds the lead by email/phone, pulls all conversations linked to that lead,
    and returns messages merged by timestamp.
    """
    result = resolve_contact(contact, user_id)
    if not result["matched"]:
        return {"lead": result, "messages": [], "conversations": []}

    lead_id = result["lead_id"]
    global _engine

    with Session(_engine) as session:
        conv_rows = session.execute(
            text("""SELECT id, title, created_at, updated_at FROM conversations WHERE client_id = :lead_id ORDER BY updated_at DESC"""),
            {"lead_id": lead_id}
        ).fetchall()

        conversations = []
        all_messages = []
        for c in conv_rows:
            cinfo = {"id": str(c[0]), "title": c[1], "created_at": str(c[2]) if c[2] else "", "updated_at": str(c[3]) if c[3] else ""}
            conversations.append(cinfo)

            msg_rows = session.execute(
                text("""SELECT id, role, content, metadata, created_at FROM messages WHERE conversation_id = :conv_id ORDER BY created_at ASC"""),
                {"conv_id": str(c[0])}
            ).fetchall()

            for m in msg_rows:
                meta = m[3] or {}
                platform = meta.get("platform", "chat") if isinstance(meta, dict) else "chat"
                all_messages.append({
                    "id": str(m[0]), "role": m[1], "content": m[2][:200],
                    "platform": platform, "conversation_id": str(c[0]),
                    "created_at": str(m[4]) if m[4] else "",
                })

        all_messages.sort(key=lambda x: x.get("created_at", ""))
        return {"lead": result, "conversations": conversations, "messages": all_messages[:limit]}


def identify_contacts_for_lead(lead_id: str) -> dict:
    """Given a lead ID, return all known contact identifiers (email, phone)."""
    global _engine
    with Session(_engine) as session:
        row = session.execute(
            text("SELECT email, phone FROM leads WHERE id = :id"),
            {"id": lead_id}
        ).fetchone()
    if not row:
        return {"lead_id": lead_id, "email": None, "phone": None, "identifiers": []}
    ids = []
    if row[0]:
        ids.append({"type": "email", "value": row[0]})
    if row[1]:
        ids.append({"type": "phone", "value": row[1]})
    return {"lead_id": lead_id, "email": row[0], "phone": row[1], "identifiers": ids}
