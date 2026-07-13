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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os, json

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

# ─── Hermes Agent ────────────────────────────────────────────────────────────
from hermes.agent import get_hermes
from hermes.tools import TOOL_DEFINITIONS
from hermes.memory import profile_summary, recall, save_note, search_notes, get_skills, search_conversations as search_memory_conversations

from .config import settings
from .api.router import api_router


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


# ─── AI ──────────────────────────────────────────────────────────────────────

@app.post("/ai", response_model=AIResponse)
async def ai_endpoint(query: AIQuery):
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
async def daily_briefing():
    return {
        "text": generate_briefing(),
        "data": get_briefing_data(),
    }


# ─── Supervisor ──────────────────────────────────────────────────────────────

@app.get("/supervisor/route")
async def test_route(message: str = "Who are my hottest leads?"):
    """Test what the supervisor would route a message to."""
    decision = route(message)
    intent = classify_intent(message)
    return {
        "message": message,
        "classified_intent": intent,
        "routed_to": decision.to_dict(),
    }


@app.get("/supervisor/agents")
async def list_agents():
    """List all available specialist agents."""
    return {
        "agents": [
            {"id": k, "name": v["name"], "description": v["description"], "tool_count": len(v["tools"])}
            for k, v in AGENT_REGISTRY.items()
        ]
    }


# ─── Activity Feed ───────────────────────────────────────────────────────────

@app.get("/activity")
async def activity_feed(limit: int = 20):
    """Get the AI activity feed — every action the AI took."""
    return {"activities": get_recent_activities(limit)}


@app.get("/activity/stats")
async def activity_stats():
    """Get aggregate AI activity statistics."""
    return get_activity_stats()


# ─── Human Approval ──────────────────────────────────────────────────────────

@app.get("/approvals/pending")
async def pending_approvals():
    """Get all actions awaiting human approval."""
    return {"approvals": get_pending_approvals()}


@app.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, body: ApprovalAction):
    """Approve a pending AI action."""
    result = approve_action(approval_id, reviewer=body.reviewer, notes=body.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already reviewed")
    record_activity("Human", f"Approved: {result.get('summary', '')[:80]}", status="approved")
    return {"status": "approved", "approval": result}


# ─── Database Seed Endpoint ────────────────────────────────────────────────────

@app.post("/api/v1/seed")
async def seed_database():
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
        
        # Import and run seed — try local path first, then Docker path
        _seed_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "database", "seed.py"),
            "/packages/database/seed.py",
        ]
        _seed_path = None
        for sp in _seed_paths:
            if os.path.exists(sp):
                _seed_path = sp
                break
        if not _seed_path:
            raise FileNotFoundError(f"seed.py not found at {_seed_paths}")
        sys.path.insert(0, os.path.dirname(_seed_path))
        exec(open(_seed_path).read())
        return {"status": "seeded", "database": db_url.split("@")[1].split("/")[0]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: ApprovalAction):
    """Reject a pending AI action."""
    result = reject_action(approval_id, reviewer=body.reviewer, reason=body.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already reviewed")
    record_activity("Human", f"Rejected: {result.get('summary', '')[:80]}", status="rejected")
    return {"status": "rejected", "approval": result}


# ═══════════════════════════════════════════════════════════════════════════
# HERMES AGENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

hermes_agent = None  # Lazy init on first request

def _get_hermes():
    global hermes_agent
    if hermes_agent is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from .config import settings
        db_url = getattr(settings, 'database_url', '').replace('+asyncpg', '')
        engine = create_engine(db_url) if db_url else None
        hermes_agent = get_hermes(db_engine=engine)
    return hermes_agent


@app.post("/api/v1/hermes/chat")
async def hermes_chat(query: AIQuery):
    """Chat with the Hermes persistent agent. Controls the entire system via NL."""
    agent = _get_hermes()
    result = agent.chat(query.message)
    return result


@app.get("/api/v1/hermes/state")
async def hermes_state():
    """Get Hermes agent internal state — skills, memory, profile."""
    agent = _get_hermes()
    return {"agent": agent.get_state(), "tools": TOOL_DEFINITIONS}


@app.get("/api/v1/hermes/memory")
async def hermes_memory(query: str = ""):
    """Search Hermes memory (facts, conversations, notes)."""
    if not query:
        return {"profile": profile_summary(), "skills": get_skills()}
    facts = recall(query)
    convs = search_memory_conversations(query)
    notes = search_notes(query)
    return {"facts": facts, "conversations": convs, "notes": notes}


@app.get("/api/v1/hermes/system-overview")
async def hermes_system_overview():
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
