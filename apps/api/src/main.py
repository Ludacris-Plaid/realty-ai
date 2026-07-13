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
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "packages", "ai"))

from agent import ask
from briefing import generate_briefing, get_briefing_data
from agents.supervisor import route, AGENT_REGISTRY, classify_intent
from activity import get_recent_activities, get_activity_stats, record_activity
from approval import get_pending_approvals, approve as approve_action, reject as reject_action

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


@app.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, body: ApprovalAction):
    """Reject a pending AI action."""
    result = reject_action(approval_id, reviewer=body.reviewer, reason=body.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already reviewed")
    record_activity("Human", f"Rejected: {result.get('summary', '')[:80]}", status="rejected")
    return {"status": "rejected", "approval": result}
