"""
Gmail / Email API — Google OAuth flow + read/sync/draft.

Provides:
  GET  /gmail/auth-url       — redirect user to Google OAuth consent screen
  GET  /gmail/callback       — OAuth callback (exchanges code for tokens)
  GET  /gmail/status         — check if user's Gmail is connected
  POST /gmail/sync           — fetch latest inbox messages
  GET  /gmail/emails         — list synced emails
  GET  /gmail/emails/{id}    — get single email + full body
  POST /gmail/drafts         — create a draft reply
  POST /gmail/send           — send a reply immediately
"""

from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GMAIL_LIB = True
except ImportError:
    Credentials = None
    build = None
    HttpError = Exception
    HAS_GMAIL_LIB = False

from ...auth import TokenPayload
from .deps import require_user, optional_user
from .db import engine as _shared_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["gmail"])

# ─── Schemas ───────────────────────────────────────────────────────────

class EmailOut(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_name: str
    snippet: str
    body: str
    label_ids: list[str]
    is_unread: bool
    received_at: str
    ai_classification: str | None = None
    ai_suggested_action: str | None = None
    ai_draft_reply: str | None = None

class DraftRequest(BaseModel):
    email_id: str
    reply_body: str

class SendRequest(BaseModel):
    to: str
    subject: str
    body: str

class SyncResponse(BaseModel):
    status: str
    synced: int
    processed: int
    drafts_created: int
    message: str

# ─── Helpers ──────────────────────────────────────────────────────────

def _get_google_config():
    from ...config import settings
    return {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", ""),
    }

def _get_stored_credentials(user_id: str) -> dict | None:
    """Load Google OAuth tokens from DB for a user."""
    with Session(_shared_engine) as session:
        row = session.execute(
            text("SELECT tokens FROM google_oauth_tokens WHERE user_id = :uid AND provider = 'gmail'"),
            {"uid": user_id},
        ).fetchone()
    logger.warning(f"_get_stored_credentials: uid={user_id[:8]}... row_found={row is not None}")
    if row:
        data = row[0]
        if isinstance(data, dict):
            return data
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None
    return None

def _store_credentials(user_id: str, tokens: dict):
    """Persist Google OAuth tokens for a user."""
    with Session(_shared_engine) as session:
        existing = session.execute(
            text("SELECT id FROM google_oauth_tokens WHERE user_id = :uid AND provider = 'gmail'"),
            {"uid": user_id},
        ).fetchone()
        if existing:
            session.execute(
                text("UPDATE google_oauth_tokens SET tokens = :tokens, updated_at = NOW() WHERE id = :id"),
                {"tokens": json.dumps(tokens), "id": existing[0]},
            )
        else:
            session.execute(
                text("""
                    INSERT INTO google_oauth_tokens (id, user_id, provider, tokens, created_at, updated_at)
                    VALUES (:id, :uid, 'gmail', :tokens, NOW(), NOW())
                """),
                {"id": str(uuid.uuid4()), "uid": user_id, "tokens": json.dumps(tokens)},
            )
        session.commit()

def _ensure_oauth_table():
    """Create the google_oauth_tokens table if it doesn't exist."""
    with Session(_shared_engine) as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS google_oauth_tokens (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                provider TEXT NOT NULL DEFAULT 'gmail',
                tokens JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_oauth_user_provider ON google_oauth_tokens(user_id, provider)"))
        session.commit()

def _ensure_emails_table():
    """Create the synced_emails table if it doesn't exist."""
    with Session(_shared_engine) as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS synced_emails (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                gmail_message_id TEXT NOT NULL,
                thread_id TEXT,
                subject TEXT DEFAULT '',
                sender TEXT DEFAULT '',
                sender_name TEXT DEFAULT '',
                snippet TEXT DEFAULT '',
                body TEXT DEFAULT '',
                label_ids JSONB DEFAULT '[]',
                is_unread BOOLEAN DEFAULT true,
                received_at TIMESTAMPTZ,
                ai_classification TEXT,
                ai_suggested_action TEXT,
                ai_draft_reply TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_emails_user ON synced_emails(user_id)"))
        session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_emails_gmail_id ON synced_emails(user_id, gmail_message_id)"))
        session.commit()

def _refresh_token_if_needed(creds_dict: dict) -> dict | None:
    """Try to refresh an expired Google access token using the refresh token."""
    if not HAS_GMAIL_LIB:
        return None
    refresh_token = creds_dict.get("refresh_token")
    if not refresh_token:
        return None
    try:
        creds = Credentials(
            token=creds_dict.get("access_token", ""),
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_dict.get("client_id", ""),
            client_secret=creds_dict.get("client_secret", ""),
            scopes=creds_dict.get("scopes", [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.modify",
            ]),
        )
        if creds.expired:
            from google.auth.transport.requests import Request as GoogleRequest
            creds.refresh(GoogleRequest())
            return {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token or refresh_token,
                "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                "client_id": creds_dict.get("client_id", ""),
                "client_secret": creds_dict.get("client_secret", ""),
                "scopes": creds_dict.get("scopes", []),
            }
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
    return None

def _decode_body(payload: dict) -> str:
    """Extract plaintext body from a Gmail message payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                try:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
            if "parts" in part:
                nested = _decode_body(part)
                if nested:
                    return nested
    if "body" in payload and "data" in payload["body"]:
        try:
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""

def _extract_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""

# ─── Mock data (fallback when no Gmail connected) ──────────────────────

MOCK_EMAILS = [
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000001",
        "gmail_message_id": "msg_001",
        "thread_id": "thread_001",
        "subject": "New property inquiry - 123 Main St",
        "sender": "buyer@example.com",
        "sender_name": "Alice Johnson",
        "snippet": "I am interested in the property at 123 Main St. Is it still available? I'd like to schedule a viewing this weekend.",
        "body": "Hi there,\n\nI am interested in the property at 123 Main St. Is it still available? I'd like to schedule a viewing this weekend.\n\nBest,\nAlice Johnson\n(555) 123-4567",
        "label_ids": ["INBOX", "UNREAD"],
        "is_unread": True,
        "received_at": "2025-01-15T10:30:00Z",
        "ai_classification": "buyer_lead",
        "ai_suggested_action": "reply_with_showing",
        "ai_draft_reply": "Hi Alice,\n\nYes, 123 Main St is still available! I'd be happy to show it to you. Are you free this Saturday or Sunday? Let me know your preferred time.\n\nBest,\nYour Agent",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000002",
        "gmail_message_id": "msg_002",
        "thread_id": "thread_002",
        "subject": "Listing update request for Downtown Condo",
        "sender": "client@example.com",
        "sender_name": "Bob Martinez",
        "snippet": "Could you send me more details about the downtown listing? I'm particularly interested in HOA fees and parking.",
        "body": "Hi,\n\nCould you send me more details about the downtown listing? I'm particularly interested in HOA fees and parking.\n\nThanks,\nBob Martinez",
        "label_ids": ["INBOX"],
        "is_unread": False,
        "received_at": "2025-01-14T14:15:00Z",
        "ai_classification": "follow_up",
        "ai_suggested_action": "send_details",
        "ai_draft_reply": "Hi Bob,\n\nGreat question! The downtown condo has HOA fees of $450/month which include water, trash, and building maintenance. It comes with one dedicated parking spot in the secured garage.\n\nWould you like to schedule a tour?\n\nBest,\nYour Agent",
    },
    {
        "id": "aaaaaaaa-0000-4000-8000-000000000003",
        "gmail_message_id": "msg_003",
        "thread_id": "thread_003",
        "subject": "Re: Your mortgage pre-approval",
        "sender": "lender@bank.com",
        "sender_name": "Carol Chen",
        "snippet": "Your client Sarah Mitchell has been pre-approved for up to $650,000. The approval letter is attached.",
        "body": "Hello,\n\nYour client Sarah Mitchell has been pre-approved for up to $650,000 at 5.75% APR. The official approval letter is attached to this email.\n\nPlease let us know if you need any additional documentation.\n\nBest,\nCarol Chen\nPremier Lending",
        "label_ids": ["INBOX", "UNREAD"],
        "is_unread": True,
        "received_at": "2025-01-13T09:00:00Z",
        "ai_classification": "pre_approval",
        "ai_suggested_action": "update_lead_score",
        "ai_draft_reply": "",
    },
]

# ─── Routes ───────────────────────────────────────────────────────────

@router.get("/auth-url")
def get_auth_url(current_user: TokenPayload = Depends(require_user)):
    """Generate Google OAuth URL for connecting Gmail."""
    cfg = _get_google_config()
    if not cfg["client_id"]:
        raise HTTPException(status_code=500, detail="Google OAuth not configured (missing GOOGLE_CLIENT_ID)")
    scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]
    params = (
        f"client_id={cfg['client_id']}"
        f"&redirect_uri={cfg['redirect_uri']}"
        f"&response_type=code"
        f"&scope={' '.join(scopes)}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={current_user.sub}"
    )
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(""), error: str = Query(None)):
    """Handle Google OAuth callback — exchange code for tokens and store them."""
    cfg = _get_google_config()
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    import httpx
    import logging
    _log = logging.getLogger(__name__)
    token_data = {
        "code": code[:10] + '...',
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": cfg["redirect_uri"],
        "grant_type": "authorization_code",
    }
    # Redact code for log safety
    _token_data_send = dict(token_data)
    _token_data_send["code"] = code
    _log.warning(f"GOOGLE_AUTH: redirect_uri=[{cfg['redirect_uri']}] client_id=[{cfg['client_id'][:30]}...] code_len={len(code)}")
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data=_token_data_send)
        if resp.status_code != 200:
            _log.error(f"GOOGLE_AUTH failed: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")
        tokens = resp.json()

    # Fetch user email from Google
    user_info = {}
    if "access_token" in tokens:
        async with httpx.AsyncClient() as client:
            info_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            if info_resp.status_code == 200:
                user_info = info_resp.json()

    # Store credentials keyed by the user_id from OAuth state
    try:
        from ...auth import decode_token
        payload = decode_token(state)
        user_id = payload.sub
    except Exception:
        if "email" in user_info:
            from ...auth import get_user_by_email
            user = await get_user_by_email(user_info["email"])
            user_id = user["id"] if user else state
        else:
            user_id = state

    _store_credentials(user_id, {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_at": None,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "scopes": tokens.get("scope", "").split(),
        "email": user_info.get("email", ""),
        "name": user_info.get("name", ""),
    })

    return RedirectResponse(
        url="https://realty.indicationsmedia.com/dashboard/settings?connected=gmail",
        status_code=302,
    )


@router.get("/status")
def gmail_status(current_user: TokenPayload = Depends(require_user)):
    """Check if the current user has Gmail connected."""
    creds = _get_stored_credentials(current_user.sub)
    if not creds:
        return {"connected": False, "email": None}

    # Try refreshing if expired
    refreshed = _refresh_token_if_needed(creds)
    if refreshed:
        _store_credentials(current_user.sub, refreshed)
        creds = refreshed

    return {
        "connected": True,
        "email": creds.get("email", ""),
        "name": creds.get("name", ""),
        "has_refresh_token": bool(creds.get("refresh_token")),
    }


@router.post("/sync", response_model=SyncResponse)
def sync_emails(current_user: TokenPayload = Depends(require_user)):
    """Sync latest Gmail inbox messages, then auto-classify them."""
    creds = _get_stored_credentials(current_user.sub)
    logger.warning(f"SYNC: user_id={current_user.sub} creds_found={creds is not None}")
    if not creds:
        # Return mock sync result when not connected
        _ensure_emails_table()
        count = 0
        with Session(_shared_engine) as session:
            for mock in MOCK_EMAILS:
                existing = session.execute(
                    text("SELECT id FROM synced_emails WHERE user_id = :uid AND gmail_message_id = :gid"),
                    {"uid": current_user.sub, "gid": mock["gmail_message_id"]},
                ).fetchone()
                if not existing:
                    session.execute(
                        text("""
                            INSERT INTO synced_emails
                                (id, user_id, gmail_message_id, thread_id, subject, sender, sender_name,
                                 snippet, body, label_ids, is_unread, received_at,
                                 ai_classification, ai_suggested_action, ai_draft_reply, created_at)
                            VALUES
                                (:id, :uid, :gid, :tid, :subj, :sender, :sname,
                                 :snippet, :body, :labels, :unread, :received,
                                 :classification, :action, :draft, NOW())
                        """),
                        {
                            "id": mock["id"],
                            "uid": current_user.sub,
                            "gid": mock["gmail_message_id"],
                            "tid": mock["thread_id"],
                            "subj": mock["subject"],
                            "sender": mock["sender"],
                            "sname": mock["sender_name"],
                            "snippet": mock["snippet"],
                            "body": mock["body"],
                            "labels": json.dumps(mock["label_ids"]),
                            "unread": mock["is_unread"],
                            "received": mock["received_at"],
                            "classification": mock.get("ai_classification"),
                            "action": mock.get("ai_suggested_action"),
                            "draft": mock.get("ai_draft_reply", ""),
                        },
                    )
                    count += 1
                session.commit()
        return SyncResponse(
            status="mock",
            synced=count,
            processed=count,
            drafts_created=sum(1 for m in MOCK_EMAILS if m.get("ai_draft_reply")),
            message=f"Mock sync complete. {count} emails synced.",
        )

    # Real Gmail sync
    if not HAS_GMAIL_LIB:
        return SyncResponse(status="error", synced=0, processed=0, drafts_created=0, message="Gmail library not available")

    # Refresh if needed
    refreshed = _refresh_token_if_needed(creds)
    if refreshed:
        _store_credentials(current_user.sub, refreshed)
        creds = refreshed

    try:
        gcred = Credentials(
            token=creds["access_token"],
            refresh_token=creds.get("refresh_token", ""),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            scopes=creds.get("scopes", []),
        )
        service = build("gmail", "v1", credentials=gcred)
        results = service.users().messages().list(userId="me", maxResults=25, q="in:inbox").execute()
        messages = results.get("messages", [])

        _ensure_emails_table()
        synced_count = 0

        for msg_summary in messages:
            full = service.users().messages().get(userId="me", id=msg_summary["id"], format="full").execute()
            headers = full.get("payload", {}).get("headers", [])
            subject = _extract_header(headers, "Subject")
            sender = _extract_header(headers, "From")
            sender_name = _extract_header(headers, "From")
            received_raw = _extract_header(headers, "Date")
            ebody = _decode_body(full.get("payload", {}))
            snippet = full.get("snippet", "")
            label_ids = full.get("labelIds", [])
            is_unread = "UNREAD" in label_ids
            internal_date = full.get("internalDate", "")
            # Convert millisecond epoch to ISO timestamp
            from datetime import datetime as dt
            if internal_date and internal_date.isdigit() and len(internal_date) >= 10:
                internal_date = dt.utcfromtimestamp(int(internal_date) / 1000).isoformat() + "Z"

            with Session(_shared_engine) as session:
                existing = session.execute(
                    text("SELECT id FROM synced_emails WHERE user_id = :uid AND gmail_message_id = :gid"),
                    {"uid": current_user.sub, "gid": full["id"]},
                ).fetchone()
                if existing:
                    session.execute(
                        text("""
                            UPDATE synced_emails SET subject=:subj, snippet=:snippet, body=:body,
                                label_ids=:labels, is_unread=:unread, received_at=:received
                            WHERE id=:id
                        """),
                        {
                            "id": existing[0], "subj": subject, "snippet": snippet,
                            "body": ebody, "labels": json.dumps(label_ids),
                            "unread": is_unread, "received": internal_date,
                        },
                    )
                else:
                    email_id = str(uuid.uuid4())
                    session.execute(
                        text("""
                            INSERT INTO synced_emails
                                (id, user_id, gmail_message_id, thread_id, subject, sender, sender_name,
                                 snippet, body, label_ids, is_unread, received_at, created_at)
                            VALUES
                                (:id, :uid, :gid, :tid, :subj, :sender, :sname,
                                 :snippet, :body, :labels, :unread, :received, NOW())
                        """),
                        {
                            "id": email_id, "uid": current_user.sub,
                            "gid": full["id"], "tid": full.get("threadId", ""),
                            "subj": subject, "sender": sender, "sname": sender_name,
                            "snippet": snippet, "body": ebody,
                            "labels": json.dumps(label_ids), "unread": is_unread,
                            "received": internal_date,
                        },
                    )
                    synced_count += 1
                session.commit()
        return SyncResponse(
            status="ok",
            synced=synced_count,
            processed=synced_count,
            drafts_created=0,
            message=f"Synced {synced_count} new emails from Gmail.",
        )

    except HttpError as e:
        logger.error(f"Gmail sync error: {e}")
        return SyncResponse(status="error", synced=0, processed=0, drafts_created=0, message=str(e))


@router.get("/emails")
def list_emails(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    classification: str = Query(None),
    current_user: TokenPayload = Depends(require_user),
):
    """List synced emails for the current user."""
    _ensure_emails_table()
    query = "SELECT * FROM synced_emails WHERE user_id = :uid"
    params: dict = {"uid": current_user.sub}
    if unread_only:
        query += " AND is_unread = true"
    if classification:
        query += " AND ai_classification = :cls"
        params["cls"] = classification
    query += " ORDER BY received_at DESC NULLS LAST, created_at DESC LIMIT :limit"
    params["limit"] = limit

    with Session(_shared_engine) as session:
        rows = session.execute(text(query), params).fetchall()

    emails = []
    for r in rows:
        label_ids_raw = r.label_ids if hasattr(r, "label_ids") else "[]"
        try:
            labels = json.loads(label_ids_raw) if isinstance(label_ids_raw, str) else label_ids_raw
        except (json.JSONDecodeError, TypeError):
            labels = []
        emails.append(EmailOut(
            id=str(r.id),
            thread_id=r.thread_id or "",
            subject=r.subject or "",
            sender=r.sender or "",
            sender_name=r.sender_name or "",
            snippet=r.snippet or "",
            body=r.body or "",
            label_ids=labels,
            is_unread=bool(r.is_unread),
            received_at=r.received_at.isoformat() if r.received_at else "",
            ai_classification=r.ai_classification,
            ai_suggested_action=r.ai_suggested_action,
            ai_draft_reply=r.ai_draft_reply,
        ))

    return {"emails": emails, "total": len(emails)}


@router.get("/emails/{email_id}")
def get_email(email_id: str, current_user: TokenPayload = Depends(require_user)):
    """Get a single synced email by ID."""
    _ensure_emails_table()
    with Session(_shared_engine) as session:
        row = session.execute(
            text("SELECT * FROM synced_emails WHERE id = :id AND user_id = :uid"),
            {"id": email_id, "uid": current_user.sub},
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Email not found")
    label_ids_raw = row.label_ids if hasattr(row, "label_ids") else "[]"
    try:
        labels = json.loads(label_ids_raw) if isinstance(label_ids_raw, str) else label_ids_raw
    except (json.JSONDecodeError, TypeError):
        labels = []
    return EmailOut(
        id=str(row.id),
        thread_id=row.thread_id or "",
        subject=row.subject or "",
        sender=row.sender or "",
        sender_name=row.sender_name or "",
        snippet=row.snippet or "",
        body=row.body or "",
        label_ids=labels,
        is_unread=bool(row.is_unread),
        received_at=row.received_at.isoformat() if row.received_at else "",
        ai_classification=row.ai_classification,
        ai_suggested_action=row.ai_suggested_action,
        ai_draft_reply=row.ai_draft_reply,
    )


@router.post("/drafts")
def create_draft(body: DraftRequest, current_user: TokenPayload = Depends(require_user)):
    """Create a draft reply for an email."""
    creds = _get_stored_credentials(current_user.sub)
    if creds and HAS_GMAIL_LIB:
        refreshed = _refresh_token_if_needed(creds)
        if refreshed:
            _store_credentials(current_user.sub, refreshed)
            creds = refreshed
        try:
            gcred = Credentials(
                token=creds["access_token"],
                refresh_token=creds.get("refresh_token", ""),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
            )
            service = build("gmail", "v1", credentials=gcred)
            msg = MIMEText(body.reply_body)
            msg["To"] = ""
            msg["Subject"] = ""
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
            return {"status": "ok", "draft_id": draft["id"]}
        except HttpError as e:
            logger.error(f"Gmail draft error: {e}")

    # Mock fallback
    with Session(_shared_engine) as session:
        session.execute(
            text("UPDATE synced_emails SET ai_draft_reply = :draft WHERE id = :id AND user_id = :uid"),
            {"id": body.email_id, "uid": current_user.sub, "draft": body.reply_body},
        )
        session.commit()
    return {"status": "ok", "draft_id": f"draft_mock_{uuid.uuid4().hex[:8]}", "mock": True}


@router.post("/send")
def send_email(body: SendRequest, current_user: TokenPayload = Depends(require_user)):
    """Send an email immediately via Gmail."""
    creds = _get_stored_credentials(current_user.sub)
    if not creds or not HAS_GMAIL_LIB:
        return {"status": "mock_sent", "to": body.to, "subject": body.subject, "mock": True}

    refreshed = _refresh_token_if_needed(creds)
    if refreshed:
        _store_credentials(current_user.sub, refreshed)
        creds = refreshed

    try:
        gcred = Credentials(
            token=creds["access_token"],
            refresh_token=creds.get("refresh_token", ""),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
        service = build("gmail", "v1", credentials=gcred)
        msg = MIMEText(body.body)
        msg["To"] = body.to
        msg["Subject"] = body.subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"status": "ok", "id": sent["id"], "to": body.to, "thread_id": sent.get("threadId", "")}
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Failed to send: {e}")


@router.get("/drafts")
def list_drafts(
    status: str = "",
    current_user: TokenPayload = Depends(require_user),
):
    """List emails with AI-generated draft replies."""
    with Session(_shared_engine) as session:
        query = ("SELECT id, sender, sender_name, subject, snippet, ai_draft_reply, "
                 "ai_classification, ai_suggested_action, thread_id, received_at "
                 "FROM synced_emails WHERE user_id = :uid AND ai_draft_reply IS NOT NULL AND ai_draft_reply != ''")
        params = {"uid": current_user.sub}
        if status == "pending":
            query += " AND (ai_suggested_action IS NULL OR ai_suggested_action != 'sent')"
        elif status == "sent":
            query += " AND ai_suggested_action = 'sent'"
        query += " ORDER BY received_at DESC"
        rows = session.execute(text(query), params).fetchall()

    return [
        {
            "id": str(r[0]),
            "to_recipient": r[1],
            "sender_name": r[2],
            "subject": r[3],
            "body": r[5],
            "ai_confidence": 85,
            "ai_classification": r[6],
            "ai_suggested_action": r[7],
            "thread_id": r[8],
            "received_at": r[9].isoformat() if r[9] else None,
        }
        for r in rows
    ]


@router.post("/drafts/{draft_id}/approve")
def approve_draft(
    draft_id: str,
    edited_body: str = "",
    current_user: TokenPayload = Depends(require_user),
):
    """Approve and send an AI draft reply."""
    body_to_send = edited_body if edited_body else None
    with Session(_shared_engine) as session:
        row = session.execute(
            text("SELECT sender, subject, ai_draft_reply, gmail_message_id, thread_id FROM synced_emails "
                 "WHERE id = :id AND user_id = :uid"),
            {"id": draft_id, "uid": current_user.sub},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Draft not found")

        draft_text = body_to_send or row[2]
        creds = _get_stored_credentials(current_user.sub)
        sent = False
        if creds and HAS_GMAIL_LIB:
            try:
                from email.mime.text import MIMEText
                from google.oauth2.credentials import Credentials as GCred
                from googleapiclient.discovery import build
                gcred = GCred(
                    token=creds["access_token"], refresh_token=creds.get("refresh_token", ""),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=creds["client_id"], client_secret=creds["client_secret"],
                )
                service = build("gmail", "v1", credentials=gcred)
                msg = MIMEText(draft_text)
                msg["To"] = row[0]
                msg["Subject"] = f"Re: {row[1]}"
                msg["In-Reply-To"] = row[3]
                rfc_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                service.users().messages().send(userId="me", body={"raw": rfc_msg}).execute()
                sent = True
            except Exception:
                pass

        session.execute(
            text("UPDATE synced_emails SET ai_suggested_action = 'sent' WHERE id = :id AND user_id = :uid"),
            {"id": draft_id, "uid": current_user.sub},
        )
        session.commit()

    return {"status": "approved", "sent": sent, "recipient": row[0], "subject": row[1]}


@router.post("/drafts/{draft_id}/reject")
def reject_draft(
    draft_id: str,
    current_user: TokenPayload = Depends(require_user),
):
    """Reject an AI draft reply (clear it)."""
    with Session(_shared_engine) as session:
        session.execute(
            text("UPDATE synced_emails SET ai_draft_reply = NULL, ai_suggested_action = 'rejected' "
                 "WHERE id = :id AND user_id = :uid"),
            {"id": draft_id, "uid": current_user.sub},
        )
        session.commit()
    return {"status": "rejected"}


# ═══════════════════════════════════════════════════════════════════════
# EMAIL MANAGEMENT ENDPOINTS (trash, spam, mark read, classify, scan)
# ═══════════════════════════════════════════════════════════════════════


class EmailActionRequest(BaseModel):
    action: str  # "trash" | "delete" | "spam"


class EmailPatchRequest(BaseModel):
    is_unread: bool | None = None
    ai_classification: str | None = None
    ai_suggested_action: str | None = None


_SPAM_KEYWORDS = [
    "buy now", "limited time", "act now", "congratulations", "you won", "winner",
    "free money", "click here", "urgent", "exclusive offer", "guaranteed",
    "no risk", "act fast", "don't miss", "clearance", "cash bonus",
    "earn extra", "work from home", "make money", "million dollars",
    "investment opportunity", "unsecured debt", "credit score",
    "refinance", "consolidate debt", "pre-approved", "pre approved",
    "viagra", "cialis", "pharmacy", "prescription", "weight loss",
]

_SPAM_SENDERS = [
    "noreply@", "no-reply@", "newsletter@", "marketing@", "mail@",
    "mailer@", "bounce@", "spam@", "promotions@",
]

_SPAM_DOMAINS = [
    "mailchimp.com", "sendgrid.net", "hubspot.com", "salesforce.com",
    "constantcontact.com", "mailerlite.com", "convertkit.com",
]


def _detect_spam(email_row) -> tuple[bool, str]:
    """Check an email for spam indicators. Returns (is_spam, reason)."""
    subj = (email_row.get("subject") or "").lower()
    sender = (email_row.get("sender") or "").lower()
    body = (email_row.get("body") or "").lower()[:500]
    combined = f"{subj} {body}"

    for kw in _SPAM_KEYWORDS:
        if kw in combined:
            return True, f"Spam keyword: '{kw}'"

    for s in _SPAM_SENDERS:
        if sender.startswith(s):
            return True, f"Suspicious sender pattern: {s}"

    for d in _SPAM_DOMAINS:
        if d in sender:
            return True, f"Known mass-mailer domain: {d}"

    return False, ""


@router.delete("/emails/{email_id}")
def delete_email(
    email_id: str,
    current_user: TokenPayload = Depends(require_user),
):
    """Permanently delete a synced email from local DB."""
    _ensure_emails_table()
    with Session(_shared_engine) as session:
        row = session.execute(
            text("SELECT gmail_message_id FROM synced_emails WHERE id = :id AND user_id = :uid"),
            {"id": email_id, "uid": current_user.sub},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Email not found")

        # Also trash in Gmail if connected
        creds = _get_stored_credentials(current_user.sub)
        if creds and HAS_GMAIL_LIB:
            try:
                gcred = Credentials(
                    token=creds["access_token"],
                    refresh_token=creds.get("refresh_token", ""),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=creds["client_id"],
                    client_secret=creds["client_secret"],
                )
                service = build("gmail", "v1", credentials=gcred)
                service.users().messages().trash(userId="me", id=row[0]).execute()
            except Exception as e:
                logger.warning(f"Gmail trash failed (DB delete continues): {e}")

        session.execute(
            text("DELETE FROM synced_emails WHERE id = :id AND user_id = :uid"),
            {"id": email_id, "uid": current_user.sub},
        )
        session.commit()

    return {"status": "deleted", "id": email_id}


@router.patch("/emails/{email_id}")
def patch_email(
    email_id: str,
    body: EmailPatchRequest,
    current_user: TokenPayload = Depends(require_user),
):
    """Update email properties: mark read/unread, change classification."""
    _ensure_emails_table()
    updates = []
    params: dict = {"id": email_id, "uid": current_user.sub}

    if body.is_unread is not None:
        updates.append("is_unread = :unread")
        params["unread"] = body.is_unread
    if body.ai_classification is not None:
        updates.append("ai_classification = :cls")
        params["cls"] = body.ai_classification
    if body.ai_suggested_action is not None:
        updates.append("ai_suggested_action = :action")
        params["action"] = body.ai_suggested_action

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE synced_emails SET {', '.join(updates)} WHERE id = :id AND user_id = :uid"
    with Session(_shared_engine) as session:
        result = session.execute(text(query), params)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Email not found")
        session.commit()

    return {"status": "updated", "id": email_id}


@router.post("/emails/{email_id}/spam")
def report_spam(
    email_id: str,
    current_user: TokenPayload = Depends(require_user),
):
    """Mark email as spam in Gmail and delete from local inbox."""
    _ensure_emails_table()
    with Session(_shared_engine) as session:
        row = session.execute(
            text("SELECT gmail_message_id FROM synced_emails WHERE id = :id AND user_id = :uid"),
            {"id": email_id, "uid": current_user.sub},
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Email not found")
        gmail_id = row[0]

        # Report spam in Gmail if connected
        creds = _get_stored_credentials(current_user.sub)
        spam_reported = False
        if creds and HAS_GMAIL_LIB:
            try:
                gcred = Credentials(
                    token=creds["access_token"],
                    refresh_token=creds.get("refresh_token", ""),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=creds["client_id"],
                    client_secret=creds["client_secret"],
                )
                service = build("gmail", "v1", credentials=gcred)
                service.users().messages().modify(
                    userId="me", id=gmail_id,
                    body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]},
                ).execute()
                spam_reported = True
            except Exception as e:
                logger.warning(f"Gmail spam report failed: {e}")

        # Remove from local inbox
        session.execute(
            text("DELETE FROM synced_emails WHERE id = :id AND user_id = :uid"),
            {"id": email_id, "uid": current_user.sub},
        )
        session.commit()

    return {
        "status": "spam_reported" if spam_reported else "deleted_locally",
        "id": email_id,
        "gmail_spam_reported": spam_reported,
    }


@router.post("/scan-spam")
def scan_inbox_for_spam(
    current_user: TokenPayload = Depends(require_user),
):
    """Scan all synced inbox emails for spam and delete them automatically."""
    _ensure_emails_table()
    with Session(_shared_engine) as session:
        rows = session.execute(
            text("""
                SELECT id, gmail_message_id, subject, sender, body
                FROM synced_emails
                WHERE user_id = :uid AND
                      (ai_classification IS NULL OR ai_classification NOT IN ('spam', 'spam_detected'))
                ORDER BY received_at DESC
            """),
            {"uid": current_user.sub},
        ).fetchall()

    deleted = 0
    spam_ids = []
    creds = _get_stored_credentials(current_user.sub)

    # Build Gmail service once if connected
    gmail_service = None
    if creds and HAS_GMAIL_LIB:
        try:
            gcred = Credentials(
                token=creds["access_token"],
                refresh_token=creds.get("refresh_token", ""),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
            )
            gmail_service = build("gmail", "v1", credentials=gcred)
        except Exception:
            pass

    for row in rows:
        row_dict = {"subject": row.subject, "sender": row.sender, "body": row.body}
        is_spam, reason = _detect_spam(row_dict)
        if is_spam:
            spam_ids.append(row.id)
            # Mark in DB
            with Session(_shared_engine) as session:
                session.execute(
                    text("""
                        UPDATE synced_emails
                        SET ai_classification = 'spam_detected',
                            ai_suggested_action = 'auto_deleted'
                        WHERE id = :id AND user_id = :uid
                    """),
                    {"id": row.id, "uid": current_user.sub},
                )
                session.commit()

            # Report spam in Gmail
            if gmail_service and row.gmail_message_id:
                try:
                    gmail_service.users().messages().modify(
                        userId="me", id=row.gmail_message_id,
                        body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]},
                    ).execute()
                except Exception:
                    pass

            # Delete from local inbox
            with Session(_shared_engine) as session:
                session.execute(
                    text("DELETE FROM synced_emails WHERE id = :id AND user_id = :uid"),
                    {"id": row.id, "uid": current_user.sub},
                )
                session.commit()
            deleted += 1

    if deleted == 0:
        return {"status": "clean", "deleted": 0, "message": "Inbox looks clean. No spam detected."}

    return {
        "status": "cleaned",
        "deleted": deleted,
        "message": f"Found and removed {deleted} spam email(s) from your inbox."
    }
