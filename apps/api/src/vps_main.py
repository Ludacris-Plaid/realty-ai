"""
RealtyAI — VPS Backend (calendar + reminders + auth + data).
Stripped of AI agent imports for VPS compatibility.
"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os, json, logging, uuid as _uuid

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://realtyai:realtyai@localhost:5432/realtyai")
# Fix common dialect aliases
for old, new in [("+asyncpg", ""), ("+psycopg2", ""), ("+psycopg", ""), ("postgresql2://", "postgresql://")]:
    DATABASE_URL = DATABASE_URL.replace(old, new)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://185.80.130.197,https://realty.indicationsmedia.com").split(",")


# ─── Auth (simplified JWT) ────────────────────────────────────────────

import jwt as _jwt
from datetime import datetime, timedelta

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class TokenPayload(BaseModel):
    sub: str
    email: str
    name: str
    brokerage_id: str = ""
    is_admin: bool = False


def create_access_token(user_id: str, email: str, name: str = "", brokerage_id: str = ""):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id, "email": email, "name": name,
        "brokerage_id": brokerage_id, "exp": expire,
    }
    token = _jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")
    if ENVIRONMENT == "development" and not token:
        return TokenPayload(sub="00000000-0000-0000-0000-000000000001", email="admin@realtyai.com", name="Admin", is_admin=True)
    try:
        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            sub=payload.get("sub", ""), email=payload.get("email", ""),
            name=payload.get("name", ""), brokerage_id=payload.get("brokerage_id", ""),
            is_admin=payload.get("is_admin", False),
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user_optional(request: Request):
    try:
        return get_current_user(request)
    except HTTPException:
        return None


# ─── DB helpers ────────────────────────────────────────────────────────

def _get_engine():
    from sqlalchemy import create_engine
    return create_engine(DATABASE_URL)


# ─── App ───────────────────────────────────────────────────────────────

app = FastAPI(title="RealtyAI (VPS)", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "environment": ENVIRONMENT}


# ─── Auth endpoints ────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    name: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


@app.post("/api/v1/auth/register")
async def register(body: UserCreate):
    """Register a new user."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": body.email}
            ).fetchone()
            if result:
                raise HTTPException(status_code=409, detail="Email already registered")
            uid = str(_uuid.uuid4())
            import hashlib
            pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
            conn.execute(
                text("INSERT INTO users (id, email, password_hash, full_name, created_at) VALUES (:id, :email, :pw, :name, NOW())"),
                {"id": uid, "email": body.email, "pw": pw_hash, "name": body.name or ""},
            )
            conn.commit()
        token, expires_in = create_access_token(uid, body.email, body.name)
        return {"access_token": token, "token_type": "bearer", "user_id": uid, "email": body.email, "full_name": body.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/auth/login")
async def login(body: UserLogin):
    """Authenticate user."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            import hashlib
            pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
            user = conn.execute(
                text("SELECT id, email, full_name FROM users WHERE email = :email AND password_hash = :pw"),
                {"email": body.email, "pw": pw_hash},
            ).fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
        token, expires_in = create_access_token(str(user[0]), str(user[1]), str(user[2] or ""))
        return {"access_token": token, "token_type": "bearer", "user_id": str(user[0]), "email": str(user[1]), "full_name": str(user[2] or "")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/auth/me")
async def me(current_user=Depends(get_current_user)):
    """Current user profile."""
    return {"id": current_user.sub, "email": current_user.email, "full_name": current_user.name}


@app.post("/api/v1/auth/dev-login")
async def dev_login():
    """Development login — returns a token for admin@realtyai.com."""
    token, expires_in = create_access_token("00000000-0000-0000-0000-000000000001", "admin@realtyai.com", "Admin")
    return {"access_token": token, "token_type": "bearer", "user_id": "00000000-0000-0000-0000-000000000001", "email": "admin@realtyai.com", "full_name": "Admin"}


# ─── Seed Database ─────────────────────────────────────────────────────

@app.post("/api/v1/seed")
async def seed_database(current_user=Depends(get_current_user)):
    """Ensure all DB tables exist."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            for ddl in [
                "CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, full_name TEXT, created_at TIMESTAMPTZ DEFAULT NOW())",
                "CREATE TABLE IF NOT EXISTS showings (id UUID PRIMARY KEY, lead_name TEXT NOT NULL, user_id UUID, property_address TEXT, showing_time TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW())",
                "CREATE TABLE IF NOT EXISTS campaigns (id UUID PRIMARY KEY, name TEXT NOT NULL, user_id UUID, audience TEXT DEFAULT '', status TEXT DEFAULT 'active', created_at TIMESTAMPTZ DEFAULT NOW())",
                "CREATE TABLE IF NOT EXISTS activities (id UUID PRIMARY KEY, organization_id UUID, user_id UUID, agent_name TEXT, action TEXT, intent TEXT DEFAULT 'general', model_used TEXT DEFAULT 'fast-model', status TEXT DEFAULT 'success', metadata JSONB DEFAULT '{}', created_at TIMESTAMPTZ DEFAULT NOW())",
                "CREATE TABLE IF NOT EXISTS approvals (id UUID PRIMARY KEY, action_type TEXT NOT NULL, summary TEXT NOT NULL, details JSONB DEFAULT '{}', agent_name TEXT DEFAULT 'General Assistant', status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW(), reviewed_at TIMESTAMPTZ, reviewed_by TEXT, notes TEXT)",
                "CREATE TABLE IF NOT EXISTS reminders (id UUID PRIMARY KEY, user_id UUID, event_id TEXT, title TEXT NOT NULL, description TEXT DEFAULT '', remind_at TIMESTAMPTZ NOT NULL, status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW())",
            ]:
                conn.execute(text(ddl))
            conn.commit()
        return {"status": "ok", "tables_created": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Calendar Events ───────────────────────────────────────────────────

@app.get("/api/v1/calendar/events")
async def list_events(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List calendar events from showings."""
    uid = current_user.sub if current_user else None
    try:
        engine = _get_engine()
        events = []
        with engine.connect() as conn:
            from sqlalchemy import text
            if uid:
                rows = conn.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings WHERE user_id = :uid OR user_id IS NULL ORDER BY showing_time LIMIT 20"),
                    {"uid": uid}
                ).fetchall()
            else:
                rows = conn.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings ORDER BY showing_time LIMIT 20")
                ).fetchall()
            for row in rows:
                sid, lead_name, address, showing_time, status = row
                day = 0
                time_str = "TBD"
                if showing_time:
                    try:
                        dt = datetime.fromisoformat(str(showing_time).replace("Z", ""))
                        day = dt.day
                        time_str = dt.strftime("%I:%M %p")
                    except (ValueError, TypeError):
                        import re as _re
                        dm = _re.search(r"(\d{4})-(\d{2})-(\d{2})", str(showing_time))
                        if dm:
                            day = int(dm.group(3))
                events.append({
                    "id": str(sid),
                    "title": f"Showing - {lead_name}" if lead_name else "Property Showing",
                    "day": day or datetime.utcnow().day,
                    "time": time_str,
                    "type": "showing",
                    "location": address or "TBD",
                    "client": lead_name or "Client",
                    "status": status or "pending",
                })
        return {"events": events}
    except Exception as e:
        logger.warning(f"Calendar events error: {e}")
        return {"events": []}


@app.get("/api/v1/calendar/all")
async def calendar_all(days: int = 7, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Calendar events + tasks."""
    uid = current_user.sub if current_user else None
    try:
        engine = _get_engine()
        events = []
        tasks_list = []
        with engine.connect() as conn:
            from sqlalchemy import text
            if uid:
                rows = conn.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings WHERE user_id = :uid ORDER BY showing_time LIMIT 20"),
                    {"uid": uid}
                ).fetchall()
            else:
                rows = conn.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings ORDER BY showing_time LIMIT 20")
                ).fetchall()
            for row in rows:
                sid, lead_name, address, showing_time, status = row
                events.append({
                    "id": str(sid), "title": f"Showing - {lead_name}" if lead_name else "Property Showing",
                    "start_time": str(showing_time) if showing_time else None,
                    "end_time": None, "type": "showing",
                    "location": address or "TBD", "client": lead_name or "Client", "status": status,
                })
        return {"events": events, "tasks": tasks_list}
    except Exception as e:
        logger.warning(f"Calendar all error: {e}")
        return {"events": [], "tasks": []}


# ─── Reminders ─────────────────────────────────────────────────────────

@app.get("/api/v1/calendar/reminders")
async def list_reminders(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List pending reminders."""
    uid = current_user.sub if current_user else None
    if not uid:
        return {"reminders": []}
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(
                text("SELECT id, event_id, title, description, remind_at, status, created_at FROM reminders WHERE user_id = :uid AND status = 'pending' ORDER BY remind_at ASC LIMIT 20"),
                {"uid": uid}
            ).fetchall()
            reminders = [{"id": str(r[0]), "event_id": str(r[1]) if r[1] else "", "title": r[2],
                          "description": r[3] or "", "remind_at": str(r[4]) if r[4] else "",
                          "status": r[5], "created_at": str(r[6]) if r[6] else ""} for r in rows]
        return {"reminders": reminders}
    except Exception as e:
        logger.warning(f"Reminders list error: {e}")
        return {"reminders": []}


@app.get("/api/v1/calendar/reminders/all")
async def list_all_reminders(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List all reminders (pending + dismissed)."""
    uid = current_user.sub if current_user else None
    if not uid:
        return {"reminders": []}
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(
                text("SELECT id, event_id, title, description, remind_at, status, created_at FROM reminders WHERE user_id = :uid ORDER BY remind_at DESC LIMIT 50"),
                {"uid": uid}
            ).fetchall()
            reminders = [{"id": str(r[0]), "event_id": str(r[1]) if r[1] else "", "title": r[2],
                          "description": r[3] or "", "remind_at": str(r[4]) if r[4] else "",
                          "status": r[5], "created_at": str(r[6]) if r[6] else ""} for r in rows]
        return {"reminders": reminders}
    except Exception as e:
        logger.warning(f"Reminders all error: {e}")
        return {"reminders": []}


@app.post("/api/v1/calendar/reminders")
async def create_reminder(body: dict, current_user=Depends(get_current_user)):
    """Create a reminder."""
    try:
        engine = _get_engine()
        rid = str(_uuid.uuid4())
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(
                text("INSERT INTO reminders (id, user_id, event_id, title, description, remind_at, status, created_at) VALUES (:id, :uid, :eid, :title, :desc, :remind_at, 'pending', NOW())"),
                {"id": rid, "uid": current_user.sub, "eid": body.get("event_id", ""),
                 "title": body.get("title", "Reminder"), "desc": body.get("description", ""),
                 "remind_at": body.get("remind_at", "")},
            )
            conn.commit()
        return {"id": rid, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/calendar/reminders/{reminder_id}")
async def update_reminder(reminder_id: str, body: dict, current_user=Depends(get_current_user)):
    """Dismiss or update a reminder."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            new_status = body.get("status", "dismissed")
            conn.execute(
                text("UPDATE reminders SET status = :status WHERE id = :id AND user_id = :uid"),
                {"status": new_status, "id": reminder_id, "uid": current_user.sub},
            )
            conn.commit()
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/calendar/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, current_user=Depends(get_current_user)):
    """Delete a reminder."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(
                text("DELETE FROM reminders WHERE id = :id AND user_id = :uid"),
                {"id": reminder_id, "uid": current_user.sub},
            )
            conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Leads ─────────────────────────────────────────────────────────────

@app.get("/api/v1/leads")
async def list_leads(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List leads."""
    uid = current_user.sub if current_user else None
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            if uid:
                rows = conn.execute(
                    text("SELECT id, first_name, last_name, email, phone, status, ai_score, created_at FROM leads WHERE agent_id = :uid ORDER BY created_at DESC LIMIT 50"),
                    {"uid": uid}
                ).fetchall()
            else:
                rows = conn.execute(
                    text("SELECT id, first_name, last_name, email, phone, status, ai_score, created_at FROM leads ORDER BY created_at DESC LIMIT 50")
                ).fetchall()
        return {"leads": [{"id": str(r[0]), "first_name": r[1], "last_name": r[2], "email": r[3],
                          "phone": r[4], "status": r[5], "ai_score": r[6], "created_at": str(r[7]) if r[7] else ""} for r in rows]}
    except Exception as e:
        logger.warning(f"Leads list error: {e}")
        return {"leads": []}


# ─── Settings / Profile ────────────────────────────────────────────────

@app.get("/api/v1/settings/profile")
async def get_profile(current_user=Depends(get_current_user)):
    """Get user profile."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            user = conn.execute(
                text("SELECT id, email, full_name FROM users WHERE id = :uid"),
                {"uid": current_user.sub}
            ).fetchone()
            if user:
                return {"id": str(user[0]), "email": str(user[1]), "full_name": str(user[2] or ""), "is_admin": True}
        return {"id": current_user.sub, "email": current_user.email, "full_name": current_user.name, "is_admin": current_user.is_admin}
    except Exception:
        return {"id": current_user.sub, "email": current_user.email, "full_name": current_user.name, "is_admin": True}


@app.get("/api/v1/athena/system-overview")
async def system_overview(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """System overview counts."""
    uid = current_user.sub if current_user else None
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            leads = conn.execute(text("SELECT COUNT(*) FROM leads" + (" WHERE agent_id = :uid" if uid else "")), ({"uid": uid} if uid else {})).scalar() or 0
            hot = conn.execute(text("SELECT COUNT(*) FROM leads WHERE ai_score >= 80" + (" AND agent_id = :uid" if uid else "")), ({"uid": uid} if uid else {})).scalar() or 0
            listings = conn.execute(text("SELECT COUNT(*) FROM properties" + (" WHERE agent_id = :uid" if uid else "")), ({"uid": uid} if uid else {})).scalar() or 0
        return {"business": {"total_leads": leads, "hot_leads": hot, "total_listings": listings, "active_listings": 0}}
    except Exception:
        return {"business": {"total_leads": 0, "hot_leads": 0, "total_listings": 0, "active_listings": 0}}


# ─── Properties ────────────────────────────────────────────────────────

@app.get("/api/v1/properties")
async def list_properties(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List properties."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(text("SELECT id, address, price, bedrooms, bathrooms, sqft, status, property_type, city, latitude, longitude, description, image_url, listed_at FROM properties ORDER BY listed_at DESC LIMIT 50")).fetchall()
        return {"properties": [{"id": str(r[0]), "address": r[1], "price": float(r[2]) if r[2] else 0, "bedrooms": r[3], "bathrooms": r[4],
                                "sqft": r[5], "status": r[6], "type": r[7], "city": r[8]} for r in rows]}
    except Exception as e:
        logger.warning(f"Properties list error: {e}")
        return {"properties": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
