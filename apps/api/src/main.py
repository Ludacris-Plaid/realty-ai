"""
RealtyAI — FastAPI Application.

Endpoints:
  GET  /health              — Health check
  POST /ai                  — Primary AI endpoint (multi-agent)
  GET  /briefing            — Daily AI Briefing
  GET  /supervisor/route    — Test supervisor routing
  GET  /supervisor/agents   — List all specialist agents
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

from agent import ask
from briefing import generate_briefing, get_briefing_data
from agents.supervisor import route, AGENT_REGISTRY, classify_intent
from activity import get_recent_activities, get_activity_stats, record_activity
from approval import get_pending_approvals, approve as approve_action, reject as reject_action

# ─── Athena Agent ──────────────────────────────────────────────────────────────
from hermes.agent import get_athena
from hermes.tools import TOOL_DEFINITIONS
from hermes.memory import profile_summary, recall, save_note, search_notes, get_skills, search_conversations as search_memory_conversations, get_conversation_messages as get_mem_conversation_messages, list_conversations as list_mem_conversations, get_bot_config, save_bot_config, delete_bot_config, list_bot_configs
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


class AIResponse(BaseModel):
    response: str
    tool_calls: list[str] = []
    model_used: str = "fast-model"
    supervisor: dict | None = None


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
    
    token, expires_in = create_access_token(user["id"], user["email"], brokerage_id=user.get("brokerage_id"))
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
    
    token, expires_in = create_access_token(user["id"], user["email"], brokerage_id=user.get("brokerage_id"))
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


# ─── AI ──────────────────────────────────────────────────────────────────────

@app.post("/ai", response_model=AIResponse)
async def ai_endpoint(query: AIQuery, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Primary AI endpoint. Routes through the Supervisor to the right specialist.
    
    The supervisor classifies intent and routes to:
      lead, marketing, listing, transaction, document, research, or general.
    """
    try:
        result = ask(query.message, override_model=query.override_model)
        tool_calls = list(set(
            tc.get("name", "unknown")
            for msg in result.get("messages", [])
            if hasattr(msg, "tool_calls") and msg.tool_calls
            for tc in msg.tool_calls
        ))
        return AIResponse(
            response=result.get("response", ""),
            tool_calls=tool_calls,
            model_used=result.get("model_used", "unknown"),
            supervisor=result.get("supervisor"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Briefing ────────────────────────────────────────────────────────────────

@app.get("/briefing")
async def daily_briefing(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    return {
        "text": generate_briefing(),
        "data": get_briefing_data(),
    }


# ─── Supervisor ──────────────────────────────────────────────────────────────

@app.get("/supervisor/route")
async def test_route(message: str = "Who are my hottest leads?", current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Test what the supervisor would route a message to."""
    decision = route(message)
    intent = classify_intent(message)
    return {
        "message": message,
        "classified_intent": intent,
        "routed_to": decision.to_dict(),
    }


@app.get("/supervisor/agents")
async def list_agents(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List all available specialist agents."""
    return {
        "agents": [
            {"id": k, "name": v["name"], "description": v["description"], "tool_count": len(v["tools"])}
            for k, v in AGENT_REGISTRY.items()
        ]
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


# ─── Database Seed Endpoint ────────────────────────────────────────────────────

@app.post("/api/v1/seed")
async def seed_database(current_user: TokenPayload = Depends(get_current_user)):
    """Seed the database with demo data for new users/organizations."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from .config import settings
        
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url)
        
        # Create vector extension
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        # Import database ORM models
        # PYTHONPATH has /packages/database/src as first entry for this
        from base import Base
        from models import User, Lead, Property, AgentProfile, Client, Document, Conversation, Message, AIMemory, Workflow, WorkflowStep, AthenaFact, AthenaConvThread, AthenaChatMessage, AthenaConversation, AthenaSkill, AthenaNote, AthenaBotConfig
        Base.metadata.create_all(engine)
        
        # Create operational tables (raw SQL — not yet in ORM models)
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id UUID PRIMARY KEY, name TEXT NOT NULL,
                    audience TEXT DEFAULT '', status TEXT DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS showings (
                    id UUID PRIMARY KEY, lead_name TEXT NOT NULL,
                    property_address TEXT, showing_time TEXT, status TEXT DEFAULT 'pending',
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
        
        # Seed data
        import uuid
        from datetime import datetime
        
        with Session(engine) as session:
            # Check if already seeded
            existing = session.execute(text("SELECT COUNT(*) FROM leads")).scalar()
            if existing and existing > 0:
                return {"status": "already_seeded", "count": existing}
            
            org_id = uuid.uuid4()
            agent_id = uuid.uuid4()
            
            agent = User(
                id=agent_id, brokerage_id=org_id, email="sarah@eliterealty.com",
                full_name="Sarah Chen", password_hash="seed-user-no-login",
                role="agent", created_at=datetime.utcnow(),
            )
            session.add(agent)
            
            profile = AgentProfile(
                id=uuid.uuid4(), user_id=agent_id,
                brokerage_name="Edmonton Elite Realty",
                brokerage_phone="(555) 123-4567",
                license_number="RE12345", created_at=datetime.utcnow(),
            )
            session.add(profile)
            
            leads = [
                Lead(id=uuid.uuid4(), first_name="Mike", last_name="Chen", email="mike.chen@email.com",
                     phone="(555) 111-2222", source="ZILLOW", status="NEW",
                     budget=720000, location_interest="Windermere", property_type_interest="Single Family",
                     timeline="Immediate", pre_approved=True, ai_score=92, ai_score_reason="Cash buyer, pre-approved, immediate timeline",
                     notes="Pre-approved, cash buyer, ready to close.", created_at=datetime.utcnow()),
                Lead(id=uuid.uuid4(), first_name="John", last_name="Smith", email="john.smith@email.com",
                     phone="(555) 222-3333", source="REFERRAL", status="QUALIFYING",
                     budget=550000, location_interest="Ambleside", property_type_interest="Townhouse",
                     timeline="30 days", pre_approved=True, ai_score=87, ai_score_reason="Pre-approved, referred by past client",
                     notes="Pre-approved, active within 30 days, responds quickly.", created_at=datetime.utcnow()),
                Lead(id=uuid.uuid4(), first_name="Emily", last_name="Davis", email="emily.davis@email.com",
                     phone="(555) 333-4444", source="WEBSITE", status="QUALIFIED",
                     budget=850000, location_interest="Rutherford", property_type_interest="Single Family",
                     timeline="60 days", pre_approved=True, ai_score=78, ai_score_reason="Referred by past client, pre-approved",
                     notes="Referred by past client, pre-approved, specific requirements.", created_at=datetime.utcnow()),
                Lead(id=uuid.uuid4(), first_name="Robert", last_name="Wilson", email="robert.wilson@email.com",
                     phone="(555) 444-5555", source="REDFIN", status="CONTACTED",
                     budget=620000, location_interest="Keswick", property_type_interest="Duplex",
                     timeline="45 days", pre_approved=False, ai_score=55, ai_score_reason="Attended open house, needs pre-approval",
                     notes="Attended open house, needs pre-approval, moderate interest.", created_at=datetime.utcnow()),
                Lead(id=uuid.uuid4(), first_name="Sarah", last_name="Johnson", email="sarah.j@email.com",
                     phone="(555) 555-6666", source="ZILLOW", status="NEW",
                     budget=350000, location_interest="Laurier Heights", property_type_interest="Condo",
                     timeline="90 days", pre_approved=False, ai_score=45, ai_score_reason="Early stage, no pre-approval yet",
                     notes="Early stage, no pre-approval yet.", created_at=datetime.utcnow()),
            ]
            for l in leads:
                session.add(l)
            
            props = [
                Property(id=uuid.uuid4(), address_street="123 Main St", address_city="Edmonton", address_state="AB", address_zip="T5J 1A4",
                         list_price=549000, beds=4, baths=3, sqft=2200, status="ACTIVE", property_type="Single Family",
                         year_built=2018, garage_spaces=2, lot_size=5200, description="Beautiful 4-bed family home in mature neighborhood."),
                Property(id=uuid.uuid4(), address_street="456 Oak Ave", address_city="Edmonton", address_state="AB", address_zip="T6H 3K1",
                         list_price=425000, beds=3, baths=2, sqft=1500, status="ACTIVE", property_type="Townhouse",
                         year_built=2015, garage_spaces=1, lot_size=2800, description="Modern townhouse with open concept layout."),
                Property(id=uuid.uuid4(), address_street="789 Pine Cres", address_city="Edmonton", address_state="AB", address_zip="T6W 2P5",
                         list_price=725000, beds=5, baths=4, sqft=3100, status="PENDING", property_type="Single Family",
                         year_built=2020, garage_spaces=3, lot_size=6800, description="Spacious executive home in Windermere."),
                Property(id=uuid.uuid4(), address_street="101 Birch Blvd", address_city="Edmonton", address_state="AB", address_zip="T5R 4E2",
                         list_price=315000, beds=2, baths=1, sqft=950, status="SOLD", property_type="Condo",
                         year_built=2005, garage_spaces=1, lot_size=0, description="Well-maintained condo near downtown."),
            ]
            for p in props:
                session.add(p)
            
            session.commit()
        
        return {"status": "seeded", "database": db_url.split("@")[1].split("/")[0]}
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
    result = agent.chat(query.message)
    # Associate the authenticated user (if any) for proactive features / personalization
    if isinstance(result, dict):
        result.setdefault("user_id", current_user.sub if current_user else None)
    return result


@app.get("/api/v1/athena/state")
async def athena_state(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get Athena agent internal state — skills, memory, profile."""
    agent = _get_athena()
    return {"agent": agent.get_state(), "tools": TOOL_DEFINITIONS}


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
            "agents": [
                {"id": k, "name": v["name"]}
                for k, v in AGENT_REGISTRY.items()
            ] if 'AGENT_REGISTRY' in dir() else [],
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


@app.get("/api/v1/athena/memories")
async def list_memories(limit: int = 50, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """List all Mem0 memories. Used for the memory dashboard."""
    if not mem0_available():
        return {"memories": [], "count": 0, "enabled": False}
    memories = mem0_get_all_memories(limit=limit)
    return {"memories": memories, "count": len(memories), "enabled": True}


@app.get("/api/v1/athena/memories/search")
async def search_memories(query: str = "", limit: int = 10, current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Semantic search across memories."""
    if not query or not mem0_available():
        return {"memories": [], "count": 0}
    results = mem0_search_memories(query, limit=limit)
    return {"memories": results, "count": len(results)}


@app.delete("/api/v1/athena/memories/{memory_id}")
async def delete_memory(memory_id: str, current_user: TokenPayload = Depends(get_current_user)):
    """Delete a specific memory by ID."""
    if not mem0_available():
        return {"ok": False, "error": "Mem0 not available"}
    ok = mem0_delete_memory(memory_id)
    return {"ok": ok, "memory_id": memory_id}


@app.get("/api/v1/athena/memories/count")
async def memory_count(current_user: Optional[TokenPayload] = Depends(get_current_user_optional)):
    """Get the count of stored memories."""
    if not mem0_available():
        return {"count": 0, "enabled": False}
    return {"count": mem0_memory_count(), "enabled": True}
