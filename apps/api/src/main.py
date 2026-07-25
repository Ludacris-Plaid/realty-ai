"""
RealtyAI — FastAPI Application.

Endpoints:
  GET  /health              — Health check
  GET  /briefing            — Daily AI Briefing
  GET  /activity            — AI activity feed
  GET  /activity/stats      — Activity statistics
  GET  /approvals/pending   — Actions needing human approval
  POST /approvals/{id}/approve — Approve an action
  POST /approvals/{id}/reject  — Reject an action
"""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os, json, logging

logger = logging.getLogger(__name__)

# Load .env into environment BEFORE any AI imports (so models.py can read them)
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("\"'")
                os.environ.setdefault(k, v)

_pkg_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "ai")
if not os.path.isdir(_pkg_path):
    _pkg_path = "/packages/ai"  # Docker layout
sys.path.insert(0, _pkg_path)

from briefing import generate_briefing, get_briefing_data
from activity import get_recent_activities, get_activity_stats, record_activity
from approval import get_pending_approvals, approve as approve_action, reject as reject_action

# ─── Athena Agent ──────────────────────────────────────────────────────────────
from hermes.agent import get_athena
from hermes.tools import TOOL_DEFINITIONS
from hermes.memory import profile_summary, get_user_profile, recall, save_note, search_notes, get_skills, search_conversations as search_memory_conversations, get_conversation_messages as get_mem_conversation_messages, list_conversations as list_mem_conversations, get_bot_config, save_bot_config, delete_bot_config, list_bot_configs
from hermes.mem0_adapter import search_memories as mem0_search_memories, get_all_memories as mem0_get_all_memories, delete_memory as mem0_delete_memory, get_user_memory_count as mem0_memory_count, is_available as mem0_available
from hermes.tools import TOOL_DEFINITIONS

# ─── Bot packages (lazy import for optional deps) ──────────────────────────

from .config import settings
from .api.router import api_router
from .auth import (
    create_access_token, get_current_user, get_current_user_optional,
    UserCreate, UserLogin, TokenResponse, UserResponse, TokenPayload,
    get_user_by_email, create_user, verify_password
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class AIQuery(BaseModel):
    message: str
    override_model: str | None = None


class ApprovalAction(BaseModel):
    reviewer: str = "Agent"
    notes: str | None = None


# ─── App ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/v1/auth/register")
async def register(body: UserCreate):
    """Register a new user account. Returns a JWT token."""
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = await create_user(body.email, body.password, body.name)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    token, expires_in = create_access_token(user["id"], user["email"], name=user.get("name", ""), brokerage_id=user.get("brokerage_id"))
    return {
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            brokerage_id=user.get("brokerage_id"),
            created_at=user["created_at"],
        ),
        "token": TokenResponse(access_token=token, expires_in=expires_in),
    }


@app.post("/api/v1/auth/login")
async def login(body: UserLogin):
    """Authenticate user and return a JWT token."""
    user = await get_user_by_email(body.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not await verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token, expires_in = create_access_token(user["id"], user["email"], name=user.get("name", ""), brokerage_id=user.get("brokerage_id"))
    return {
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            brokerage_id=user.get("brokerage_id"),
            created_at=user["created_at"],
        ),
        "token": TokenResponse(access_token=token, expires_in=expires_in),
    }


@app.get("/api/v1/auth/me")
async def me(current_user = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


# ─── Briefing ────────────────────────────────────────────────────────────────

@app.get("/briefing")
async def daily_briefing(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    name = current_user.name if current_user else ""
    return {
        "text": generate_briefing(agent_name=name),
        "data": get_briefing_data(agent_name=name),
    }


# ─── Activity Feed ───────────────────────────────────────────────────────────

@app.get("/activity")
async def activity_feed(limit: int = 20, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get the AI activity feed — every action the AI took."""
    return {"activities": get_recent_activities(limit)}


@app.get("/activity/stats")
async def activity_stats(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get aggregate AI activity statistics."""
    return get_activity_stats()


# ─── Human Approval ──────────────────────────────────────────────────────────

@app.get("/approvals/pending")
async def pending_approvals(current_user: TokenPayload = Depends(get_current_user)):
    """Get all actions awaiting human approval."""
    return {"approvals": get_pending_approvals()}


@app.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, body: ApprovalAction, current_user: TokenPayload = Depends(get_current_user)):
    """Approve a pending AI action."""
    result = approve_action(approval_id, reviewer=body.reviewer, notes=body.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already reviewed")
    record_activity("Human", f"Approved: {result.get('summary', '')[:80]}", status="approved",
                    organization_id=current_user.brokerage_id, user_id=current_user.sub)
    return {"status": "approved", "approval": result}


# ─── Database Schema Setup (no fake data) ─────────────────────────────────────

@app.post("/api/v1/seed")
async def seed_database(current_user: TokenPayload = Depends(get_current_user)):
    """Ensure all DB tables exist. No fake/demo data is created."""
    try:
        from sqlalchemy import create_engine, text
        from .config import settings
        
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        from base import Base
        Base.metadata.create_all(engine)
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id UUID PRIMARY KEY, name TEXT NOT NULL,
                    user_id UUID, audience TEXT DEFAULT '', status TEXT DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS showings (
                    id UUID PRIMARY KEY, lead_name TEXT NOT NULL,
                    user_id UUID, property_address TEXT, showing_time TEXT, status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS activities (
                    id UUID PRIMARY KEY,
                    organization_id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    intent TEXT DEFAULT 'general',
                    model_used TEXT DEFAULT 'fast-model',
                    status TEXT DEFAULT 'success',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id UUID PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details JSONB DEFAULT '{}',
                    agent_name TEXT DEFAULT 'General Assistant',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    reviewed_at TIMESTAMPTZ,
                    reviewed_by TEXT,
                    notes TEXT
                )
            """))
            conn.commit()
        
        return {"status": "ok", "tables_created": True}
    except Exception as e:
        import traceback
        return {"status": "error", "detail": f"{e}\n{traceback.format_exc()}"}


@app.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: ApprovalAction, current_user: TokenPayload = Depends(get_current_user)):
    """Reject a pending AI action."""
    result = reject_action(approval_id, reviewer=body.reviewer, reason=body.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already reviewed")
    record_activity("Human", f"Rejected: {result.get('summary', '')[:80]}", status="rejected",
                    organization_id=current_user.brokerage_id, user_id=current_user.sub)
    return {"status": "rejected", "approval": result}


# ═══════════════════════════════════════════════════════════════════════════
# ATHENA AGENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

athena_agent = None  # Lazy init on first request

def _get_athena():
    global athena_agent
    if athena_agent is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url) if db_url else None
        athena_agent = get_athena(db_engine=engine)
    return athena_agent


@app.post("/api/v1/athena/chat")
async def athena_chat(query: AIQuery, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Chat with Athena — your digital secretary. She controls the entire system via natural language."""
    agent = _get_athena()
    user_name = current_user.name if current_user else ""
    user_id = current_user.sub if current_user else ""
    result = agent.chat(query.message, user_name=user_name, user_id=user_id)
    # Associate the authenticated user for proactive features / personalization
    if isinstance(result, dict):
        result.setdefault("user_id", user_id)
    return result


@app.post("/api/v1/athena/reset-memory")
async def athena_reset_memory(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Factory reset — wipe all Athena memories, facts, conversations, and Mem0 data. Fresh slate."""
    agent = _get_athena()
    result = agent.reset_memory()
    return result


@app.get("/api/v1/athena/state")
async def athena_state(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get Athena agent internal state — skills, memory, profile."""
    agent = _get_athena()
    return {"agent": agent.get_state(), "tools": TOOL_DEFINITIONS}


# ═══════════════════════════════════════════════════════════════════════════
# SCRAPER & DATA ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════


class ScrapeRequest(BaseModel):
    location: str = "Edmonton, AB"
    count: int = 25


@app.post("/api/v1/scrape")
async def scrape_endpoint(body: ScrapeRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Scrape real property listings from Zillow and seed the database."""
    try:
        from hermes.scraper import scrape_and_seed
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        result = scrape_and_seed(
            location=body.location,
            count=max(body.count, 5),
            db_url=db_url,
            user_id=current_user.sub,
        )
        return {"status": "ok", **result}
    except Exception as e:
        import traceback
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


# ─── Calendar Events ─────────────────────────────────────────────────────


class EventOut(BaseModel):
    id: str
    title: str
    day: int
    time: str
    type: str
    location: str
    client: str
    status: str


@app.get("/api/v1/calendar/events")
async def list_events(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List calendar events from showings and activities."""
    uid = current_user.sub if current_user else None
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)
        events = []

        with Session(engine) as session:
            # Showings → calendar events
            if uid:
                showing_rows = session.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings WHERE user_id = :uid ORDER BY showing_time LIMIT 20"),
                    {"uid": uid}
                ).fetchall()
            else:
                showing_rows = session.execute(
                    text("SELECT id, lead_name, property_address, showing_time, status FROM showings ORDER BY showing_time LIMIT 20")
                ).fetchall()

            for row in showing_rows:
                sid, lead_name, address, showing_time, status = row
                # Parse day from showing_time
                day = 0
                time_str = "TBD"
                if showing_time:
                    try:
                        dt = datetime.fromisoformat(str(showing_time).replace("Z", ""))
                        day = dt.day
                        time_str = dt.strftime("%I:%M %p")
                    except (ValueError, TypeError):
                        import re as _re
                        day_match = _re.search(r"(\d{4})-(\d{2})-(\d{2})", str(showing_time))
                        if day_match:
                            day = int(day_match.group(3))

                event_type_map = {
                    "pending": "showing", "confirmed": "showing",
                    "completed": "showing", "cancelled": "showing",
                }

                events.append({
                    "id": str(sid),
                    "title": f"Showing - {lead_name}" if lead_name else "Property Showing",
                    "day": day or datetime.utcnow().day,
                    "time": time_str,
                    "type": event_type_map.get(str(status), "showing"),
                    "location": address or "TBD",
                    "client": lead_name or "Client",
                    "status": status,
                })

        return {"events": events}
    except Exception as e:
        logger.warning(f"Calendar events error: {e}")
        return {"events": []}


# ─── Campaigns ───────────────────────────────────────────────────────────


class CampaignOut(BaseModel):
    id: str
    name: str
    status: str
    type: str
    sent: int = 0
    opened: int = 0
    responded: int = 0
    audience: str = ""


@app.get("/api/v1/campaigns")
async def list_campaigns(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List marketing campaigns."""
    uid = current_user.sub if current_user else None
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)
        with Session(engine) as session:
            if uid:
                rows = session.execute(
                    text("SELECT id, name, audience, status, created_at FROM campaigns WHERE user_id = :uid ORDER BY created_at DESC LIMIT 20"),
                    {"uid": uid}
                ).fetchall()
            else:
                rows = session.execute(
                    text("SELECT id, name, audience, status, created_at FROM campaigns ORDER BY created_at DESC LIMIT 20")
                ).fetchall()
            campaigns = []
            for row in rows:
                cid, name, audience, status, created = row
                # Infer type from name
                name_lower = (name or "").lower()
                ctype = "email"
                if any(w in name_lower for w in ["social", "facebook", "instagram"]):
                    ctype = "social"
                elif any(w in name_lower for w in ["newsletter", "report"]):
                    ctype = "newsletter"
                campaigns.append({
                    "id": str(cid),
                    "name": name or "Untitled",
                    "status": status or "draft",
                    "type": ctype,
                    "audience": audience or "",
                    "sent": 0,  # Would need a tracking system
                    "opened": 0,
                    "responded": 0,
                })
            return {"campaigns": campaigns}
    except Exception as e:
        logger.warning(f"Campaigns list error: {e}")
        return {"campaigns": []}


# ─── Profile Update ──────────────────────────────────────────────────────


class ProfileUpdate(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    brokerage_name: str = ""
    brokerage_phone: str = ""
    license_number: str = ""


@app.put("/api/v1/auth/profile")
async def update_profile(body: ProfileUpdate, current_user: TokenPayload = Depends(get_current_user)):
    """Update the current user's profile."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)

        with Session(engine) as session:
            # Update user name/email
            if body.name:
                session.execute(
                    text("UPDATE users SET full_name = :name WHERE id = :uid"),
                    {"name": body.name, "uid": current_user.sub},
                )
            if body.email:
                session.execute(
                    text("UPDATE users SET email = :email WHERE id = :uid"),
                    {"email": body.email, "uid": current_user.sub},
                )
            # Update agent profile
            if any([body.phone, body.brokerage_name, body.brokerage_phone, body.license_number]):
                # Upsert agent profile
                existing = session.execute(
                    text("SELECT id FROM agent_profiles WHERE user_id = :uid"),
                    {"uid": current_user.sub},
                ).fetchone()
                if existing:
                    updates = []
                    params = {"uid": current_user.sub}
                    if body.phone:
                        updates.append("phone = :phone")
                        params["phone"] = body.phone
                    if body.brokerage_name:
                        updates.append("brokerage_name = :bn")
                        params["bn"] = body.brokerage_name
                    if body.brokerage_phone:
                        updates.append("brokerage_phone = :bp")
                        params["bp"] = body.brokerage_phone
                    if body.license_number:
                        updates.append("license_number = :ln")
                        params["ln"] = body.license_number
                    if updates:
                        session.execute(
                            text(f"UPDATE agent_profiles SET {', '.join(updates)} WHERE user_id = :uid"),
                            params,
                        )
            session.commit()

        return {"status": "saved", "message": "Profile updated successfully"}
    except Exception as e:
        logger.warning(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {e}")


# ─── Dashboard Recommendations ──────────────────────────────────────────


class RecommendationOut(BaseModel):
    title: str
    description: str
    priority: str  # high, medium, low
    action: str  # what tool or action to suggest
    category: str  # leads, listings, marketing, compliance


@app.get("/api/v1/dashboard/recommendations")
async def dashboard_recommendations(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Generate AI-powered recommendations based on current data."""
    uid = current_user.sub if current_user else None
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)
        with Session(engine) as session:
            if uid:
                lead_count = session.execute(text("SELECT COUNT(*) FROM leads WHERE agent_id = :uid"), {"uid": uid}).scalar() or 0
                hot_leads = session.execute(text("SELECT COUNT(*) FROM leads WHERE agent_id = :uid AND ai_score >= 80"), {"uid": uid}).scalar() or 0
                dormant_leads = session.execute(text("SELECT COUNT(*) FROM leads WHERE agent_id = :uid AND status = 'DORMANT'"), {"uid": uid}).scalar() or 0
                active_listings = session.execute(text("SELECT COUNT(*) FROM properties WHERE agent_id = :uid AND status = 'ACTIVE'"), {"uid": uid}).scalar() or 0
                pending_listings = session.execute(text("SELECT COUNT(*) FROM properties WHERE agent_id = :uid AND status = 'PENDING'"), {"uid": uid}).scalar() or 0
                campaign_count = session.execute(text("SELECT COUNT(*) FROM campaigns WHERE user_id = :uid AND status = 'active'"), {"uid": uid}).scalar() or 0
                recent_activities = session.execute(
                    text("SELECT COUNT(*) FROM activities WHERE user_id = :uid AND created_at >= NOW() - INTERVAL '7 days'"), {"uid": uid}
                ).scalar() or 0
            else:
                lead_count = session.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0
                hot_leads = session.execute(text("SELECT COUNT(*) FROM leads WHERE ai_score >= 80")).scalar() or 0
                dormant_leads = session.execute(text("SELECT COUNT(*) FROM leads WHERE status = 'DORMANT'")).scalar() or 0
                active_listings = session.execute(text("SELECT COUNT(*) FROM properties WHERE status = 'ACTIVE'")).scalar() or 0
                pending_listings = session.execute(text("SELECT COUNT(*) FROM properties WHERE status = 'PENDING'")).scalar() or 0
                campaign_count = session.execute(text("SELECT COUNT(*) FROM campaigns WHERE status = 'active'")).scalar() or 0
                recent_activities = session.execute(
                    text("SELECT COUNT(*) FROM activities WHERE created_at >= NOW() - INTERVAL '7 days'")
                ).scalar() or 0
    except Exception:
        lead_count = hot_leads = dormant_leads = active_listings = 0
        pending_listings = campaign_count = recent_activities = 0

    recommendations = []

    # Lead-based recommendations
    if hot_leads > 0:
        recommendations.append(RecommendationOut(
            title=f"{hot_leads} hot lead{'s' if hot_leads > 1 else ''} ready to contact",
            description=f"You have {hot_leads} lead{'s' if hot_leads > 1 else ''} with scores over 80. They're pre-qualified and ready for follow-up. Reach out today to maximize conversion.",
            priority="high",
            action="list_leads",
            category="leads",
        ))
    if dormant_leads > 0:
        recommendations.append(RecommendationOut(
            title=f"{dormant_leads} dormant lead{'s' if dormant_leads > 1 else ''} need re-engagement",
            description=f"Your pipeline has {dormant_leads} cold lead{'s' if dormant_leads > 1 else ''}. Consider a nurture campaign or warm email to re-engage them.",
            priority="medium",
            action="analyze_pipeline",
            category="leads",
        ))

    # Listing-based recommendations
    if active_listings > 0 and active_listings < 5:
        recommendations.append(RecommendationOut(
            title="Low active inventory",
            description=f"You have {active_listings} active listings. Consider listing more properties to maintain pipeline momentum.",
            priority="medium",
            action="list_listings",
            category="listings",
        ))
    if pending_listings > 0:
        recommendations.append(RecommendationOut(
            title=f"{pending_listings} pending listing{'s' if pending_listings > 1 else ''} to close",
            description=f"You have {pending_listings} pending listing{'s' if pending_listings > 1 else ''}. Review timelines and prepare for closing.",
            priority="high",
            action="get_dashboard_summary",
            category="listings",
        ))

    # Campaign recommendations
    if campaign_count == 0:
        recommendations.append(RecommendationOut(
            title="No active campaigns",
            description="You don't have any active marketing campaigns. Launch a campaign to nurture your leads and attract new clients.",
            priority="low",
            action="launch_campaign",
            category="marketing",
        ))

    # General business health
    if lead_count > 0 and active_listings == 0:
        recommendations.append(RecommendationOut(
            title="Leads without listings",
            description=f"You have {lead_count} leads but no active listings. Consider adding properties to give your leads options.",
            priority="medium",
            action="get_dashboard_summary",
            category="listings",
        ))

    # Health check
    if recent_activities == 0:
        recommendations.append(RecommendationOut(
            title="No recent activity",
            description="There's been no system activity in the last 7 days. Ask Athena for a full system overview to check on your business.",
            priority="low",
            action="system_overview",
            category="listings",
        ))

    # Empty state — suggest first scrape
    if lead_count == 0 and active_listings == 0:
        recommendations.append(RecommendationOut(
            title="Welcome! Get started with your first scrape",
            description="Your database is empty. Scrape property listings from Zillow to populate your dashboard and start building your pipeline.",
            priority="high",
            action="scrape_properties_advanced",
            category="listings",
        ))

    return {"recommendations": recommendations}


@app.get("/api/v1/athena/memory")
async def athena_memory(query: str = "", current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Search Athena's memory (facts, conversations, notes)."""
    if not query:
        return {"profile": profile_summary(), "skills": get_skills()}
    facts = recall(query)
    convs = search_memory_conversations(query)
    notes = search_notes(query)
    return {"facts": facts, "conversations": convs, "notes": notes}


@app.get("/api/v1/athena/system-overview")
async def athena_system_overview(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Full system overview — all counts, health, agent state."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        if db_url:
            engine = create_engine(db_url)
            with Session(engine) as session:
                from sqlalchemy import text
                leads = session.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0
                listings = session.execute(text("SELECT COUNT(*) FROM properties")).scalar() or 0
                hot = session.execute(text("SELECT COUNT(*) FROM leads WHERE ai_score >= 80")).scalar() or 0
                active = session.execute(text("SELECT COUNT(*) FROM properties WHERE status = 'ACTIVE'")).scalar() or 0
        else:
            leads = listings = hot = active = 0
    except:
        leads = listings = hot = active = 0
    
    # Scope by user if authenticated
    uid = current_user.sub if current_user else None
    if uid:
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session
            from .config import settings
            db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
            if db_url:
                engine = create_engine(db_url)
                with Session(engine) as session:
                    leads = session.execute(text("SELECT COUNT(*) FROM leads WHERE agent_id = :uid"), {"uid": uid}).scalar() or 0
                    listings = session.execute(text("SELECT COUNT(*) FROM properties WHERE agent_id = :uid"), {"uid": uid}).scalar() or 0
                    hot = session.execute(text("SELECT COUNT(*) FROM leads WHERE agent_id = :uid AND ai_score >= 80"), {"uid": uid}).scalar() or 0
                    active = session.execute(text("SELECT COUNT(*) FROM properties WHERE agent_id = :uid AND status = 'ACTIVE'"), {"uid": uid}).scalar() or 0
        except:
            pass
    
    import psutil
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    
    return {
        "business": {
            "total_leads": leads,
            "hot_leads": hot,
            "total_listings": listings,
            "active_listings": active,
        },
        "system": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_gb": round(mem.used / (1024**3), 1),
            "memory_total_gb": round(mem.total / (1024**3), 1),
        },
        "ai": {
            "model": os.environ.get("LLM_DEFAULT_MODEL", "unsloth/Llama-3.2-3B-Instruct"),
            "fallback": os.environ.get("LLM_FALLBACK_MODEL", "meta/llama-3.1-8b-instruct"),
            "agents": [],
        }
    }


# ─── Persistent Conversation Endpoints ────────────────────────────────────

@app.get("/api/v1/athena/conversations")
async def list_athena_conversations(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List all past conversation threads."""
    return {"conversations": list_mem_conversations()}


@app.get("/api/v1/athena/conversations/current")
async def get_current_conversation(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get active conversation with its messages."""
    agent = _get_athena()
    messages = get_mem_conversation_messages(agent.conversation_id)
    return {"conversation_id": agent.conversation_id, "messages": messages}


@app.get("/api/v1/athena/conversations/{conv_id}/messages")
async def get_conversation_messages_endpoint(conv_id: str, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get all messages for a specific conversation."""
    messages = get_mem_conversation_messages(conv_id)
    return {"conversation_id": conv_id, "messages": messages}


@app.post("/api/v1/athena/conversations/new")
async def new_conversation(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Start a fresh conversation. The old one is preserved and can be reviewed later."""
    agent = _get_athena()
    new_id = agent.new_conversation()
    return {"conversation_id": new_id, "message": "Fresh start. I'm ready for you."}


# ═══════════════════════════════════════════════════════════════════════════
# BOT WEBHOOK ENDPOINTS (Telegram, Slack)
# ═══════════════════════════════════════════════════════════════════════════


def _route_to_athena(text: str) -> dict:
    """Route a message to the shared Athena agent."""
    agent = _get_athena()
    return agent.chat(text)


@app.post("/api/v1/athena/telegram/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook — receives messages and routes to Athena."""
    try:
        from bots.telegram import handle_update
        # Load runtime token from DB (fallback to env var)
        bot_cfg = get_bot_config("telegram")
        token = bot_cfg["config"].get("bot_token", "")
        data = await request.json()
        result = await handle_update(data, _route_to_athena, token=token)
        return result
    except ImportError as e:
        logger.error(f"Telegram bot package not installed: {e}")
        return {"ok": False, "error": f"Telegram bot not available: {e}"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": False, "error": str(e)}


@app.post("/api/v1/athena/slack/events")
async def slack_events(request: Request):
    """Slack Events API endpoint — receives events and routes to Athena."""
    try:
        from bots.slack import handle_event, verify_slack_signature
        # Load runtime tokens from DB (fallback to env var)
        bot_cfg = get_bot_config("slack")
        slack_bot_token = bot_cfg["config"].get("bot_token", "")
        slack_signing_secret = bot_cfg["config"].get("signing_secret", "")
        
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # Verify Slack signing secret
        if not verify_slack_signature(dict(request.headers), body_str, signing_secret=slack_signing_secret):
            return {"ok": False, "error": "Invalid signature"}
        
        data = json.loads(body_str)
        result = await handle_event(data, _route_to_athena, bot_token=slack_bot_token)
        return result
    except ImportError as e:
        logger.error(f"Slack bot package not installed: {e}")
        return {"ok": False, "error": f"Slack bot not available: {e}"}
    except Exception as e:
        logger.error(f"Slack events error: {e}")
        return {"ok": False, "error": str(e)}


@app.post("/api/v1/athena/telegram/set-webhook")
async def telegram_set_webhook(current_user: TokenPayload = Depends(get_current_user)):
    """Register the Telegram webhook URL (called once during setup)."""
    try:
        from bots.telegram import set_webhook
        bot_cfg = get_bot_config("telegram")
        token = bot_cfg["config"].get("bot_token", "")
        
        base_url = os.environ.get("PUBLIC_URL", "")
        if not base_url:
            base_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
            if base_url:
                base_url = f"https://{base_url}"
        if not base_url:
            return {"ok": False, "error": "PUBLIC_URL not set"}
        webhook_url = f"{base_url.rstrip('/')}/api/v1/athena/telegram/webhook"
        result = await set_webhook(webhook_url, token=token)
        return result
    except ImportError as e:
        return {"ok": False, "error": f"Telegram bot not available: {e}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/v1/athena/bots/status")
async def bot_status(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Check which bot integrations are configured (env vars + DB)."""
    from bots.telegram import is_configured as tg_configured
    from bots.slack import is_configured as slack_configured
    
    db_configs = list_bot_configs()
    
    # Check both env vars and DB configs
    tg_env = bool(os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    tg_db = db_configs.get("telegram", {}).get("enabled", False)
    slack_env = bool(os.environ.get("SLACK_BOT_TOKEN", "")) and bool(os.environ.get("SLACK_SIGNING_SECRET", ""))
    slack_db = db_configs.get("slack", {}).get("enabled", False)
    
    return {
        "telegram": {
            "configured": tg_env or tg_db,
            "env_token_set": tg_env,
            "db_configured": tg_db,
            "db_config": db_configs.get("telegram", {}),
        },
        "slack": {
            "configured": slack_env or slack_db,
            "env_bot_token_set": bool(os.environ.get("SLACK_BOT_TOKEN", "")),
            "env_signing_secret_set": bool(os.environ.get("SLACK_SIGNING_SECRET", "")),
            "db_configured": slack_db,
            "db_config": db_configs.get("slack", {}),
        },
    }


# ─── Bot Configuration Endpoints (user-managed tokens) ─────────────────────


class BotConfigRequest(BaseModel):
    platform: str
    config: dict = {}
    enabled: bool = False


@app.post("/api/v1/athena/bots/config")
async def set_bot_config(req: BotConfigRequest, current_user: TokenPayload = Depends(get_current_user)):
    """Save bot configuration tokens (Telegram, Slack, etc.)."""
    save_bot_config(req.platform, req.config, req.enabled)
    return {"ok": True, "platform": req.platform, "enabled": req.enabled}


@app.delete("/api/v1/athena/bots/config/{platform}")
async def remove_bot_config(platform: str, current_user: TokenPayload = Depends(get_current_user)):
    """Delete bot configuration for a platform."""
    delete_bot_config(platform)
    return {"ok": True, "platform": platform}


# ═══════════════════════════════════════════════════════════════════════════
# MEM0 MEMORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════


def _facts_to_memories():
    """Normalize PostgreSQL athena_facts into the same format Mem0 memories."""
    profile = get_user_profile()
    memories = []
    if profile:
        for cat, facts in profile.items():
            for f in facts:
                memories.append({
                    "id": f"pg_{cat}_{f['key']}",
                    "text": f"[{cat}] {f['key']}: {f['value']}",
                    "metadata": {"category": cat, "key": f.get("key", ""), "confidence": f.get("confidence", 1.0), "source": "postgres"},
                    "created_at": "",
                    "importance": f["confidence"],
                    "categories": [cat],
                })
    return memories


@app.get("/api/v1/athena/memories")
async def list_memories(limit: int = 50, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List all stored memories. Uses Mem0 when available, falls back to PostgreSQL facts."""
    if mem0_available():
        memories = mem0_get_all_memories(limit=limit)
        return {"memories": memories, "count": len(memories), "enabled": True}
    # Fallback: return PostgreSQL facts
    memories = _facts_to_memories()
    return {"memories": memories[:limit], "count": len(memories), "enabled": False}


@app.get("/api/v1/athena/memories/search")
async def search_memories(query: str = "", limit: int = 10, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Semantic search across memories."""
    if not query:
        return {"memories": [], "count": 0}
    if mem0_available():
        results = mem0_search_memories(query, limit=limit)
        return {"memories": results, "count": len(results)}
    # Fallback: keyword filter PostgreSQL facts
    q = query.lower()
    memories = _facts_to_memories()
    filtered = [m for m in memories if q in m["text"].lower()]
    return {"memories": filtered[:limit], "count": len(filtered)}


@app.delete("/api/v1/athena/memories/{memory_id}")
async def delete_memory(memory_id: str, current_user: TokenPayload = Depends(get_current_user)):
    """Delete a specific memory by ID."""
    if memory_id.startswith("pg_"):
        return {"ok": True, "memory_id": memory_id}  # Can't delete PG facts via this endpoint
    if not mem0_available():
        return {"ok": False, "error": "Mem0 not available"}
    ok = mem0_delete_memory(memory_id)
    return {"ok": ok, "memory_id": memory_id}


@app.get("/api/v1/athena/memories/count")
async def memory_count(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get the count of stored memories."""
    if mem0_available():
        return {"count": mem0_memory_count(), "enabled": True}
    count = len(_facts_to_memories())
    return {"count": count, "enabled": False}
