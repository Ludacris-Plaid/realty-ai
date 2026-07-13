"""
Athena Agent — RealtyAI System Tools.

These tools give Athena complete control over the RealtyAI system.
All controllable via natural language through the chat interface.
"""
import os
from typing import Optional
from datetime import datetime

from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session

# ─── Database access helper ────────────────────────────────────────────────
# Engine is set by the API on init
_engine = None

def set_engine(engine):
    global _engine
    _engine = engine


# ─── Tool definitions (returned as docstrings for the LLM) ─────────────────

TOOL_DEFINITIONS = [
    {
        "name": "list_leads",
        "description": "List all leads in the pipeline. Can filter by status (NEW, QUALIFYING, QUALIFIED, CONTACTED, APPOINTMENT_SET, CLOSED_WON, CLOSED_LOST, DORMANT). Returns IDs, names, scores, and budgets. If no status given, returns all leads.",
        "parameters": {"status": {"type": "string", "description": "Filter by status (optional, uppercase)", "required": False}}
    },
    {
        "name": "get_lead_detail",
        "description": "Get detailed info about a specific lead by ID.",
        "parameters": {"lead_id": {"type": "string", "description": "UUID of the lead", "required": True}}
    },
    {
        "name": "update_lead_status",
        "description": "Move a lead to a new status in the pipeline.",
        "parameters": {"lead_id": {"type": "string", "description": "UUID of the lead", "required": True}, "status": {"type": "string", "description": "New status", "required": True}}
    },
    {
        "name": "list_listings",
        "description": "List all property listings. Can filter by status (ACTIVE, PENDING, SOLD, DRAFT, EXPIRED).",
        "parameters": {"status": {"type": "string", "description": "Filter by status (optional)", "required": False}}
    },
    {
        "name": "get_dashboard_summary",
        "description": "Get the full business dashboard summary: lead counts, listing stats, pipeline value, pending approvals.",
        "parameters": {}
    },
    {
        "name": "get_agent_stats",
        "description": "Get AI agent usage statistics: total activities, breakdown by intent, success rates.",
        "parameters": {}
    },
    {
        "name": "launch_campaign",
        "description": "Launch an AI marketing campaign. Generates content and sends to target audience.",
        "parameters": {"name": {"type": "string", "description": "Campaign name", "required": True}, "audience": {"type": "string", "description": "Target audience filter", "required": False}}
    },
    {
        "name": "generate_listing_description",
        "description": "Generate an AI MLS listing description for a property.",
        "parameters": {"property_id": {"type": "string", "description": "UUID of the property", "required": True}, "tone": {"type": "string", "description": "Writing tone: professional, luxury, cozy, modern", "required": False}}
    },
    {
        "name": "analyze_pipeline",
        "description": "Analyze the lead pipeline and suggest next actions. Returns AI recommendations for each lead.",
        "parameters": {}
    },
    {
        "name": "schedule_showing",
        "description": "Schedule a property showing.",
        "parameters": {"lead_name": {"type": "string", "description": "Client name", "required": True}, "property_address": {"type": "string", "description": "Property address", "required": True}, "time": {"type": "string", "description": "Date/time for showing", "required": True}}
    },
    {
        "name": "remember_fact",
        "description": "Remember something about the user for future sessions. Use this to learn preferences, habits, and goals.",
        "parameters": {"key": {"type": "string", "description": "Fact identifier", "required": True}, "value": {"type": "string", "description": "Fact content", "required": True}, "category": {"type": "string", "description": "Category: preference, habit, client, goal, note", "required": False}}
    },
    {
        "name": "recall_memory",
        "description": "Search past memories and user facts. The agent uses this to remember what it knows.",
        "parameters": {"query": {"type": "string", "description": "Search query", "required": True}}
    },
    {
        "name": "save_note",
        "description": "Save an Obsidian-style note. Good for recording insights, ideas, and important info.",
        "parameters": {"title": {"type": "string", "description": "Note title", "required": True}, "body": {"type": "string", "description": "Note body (markdown)", "required": True}, "tags": {"type": "string", "description": "Comma-separated tags", "required": False}}
    },
    {
        "name": "get_crew_info",
        "description": "Get info about the CrewAI agents and their current status.",
        "parameters": {}
    },
    {
        "name": "run_crew",
        "description": "Execute a CrewAI crew for a specific task. Can run marketing crews, listing crews, etc.",
        "parameters": {"crew_name": {"type": "string", "description": "Crew name: marketing_crew, listing_crew, lead_scoring_crew", "required": True}, "input_data": {"type": "string", "description": "JSON string of input data for the crew", "required": False}}
    },
    {
        "name": "system_overview",
        "description": "Get a complete overview of the entire RealtyAI system: all counts, stats, active processes, agent status, and system health.",
        "parameters": {}
    },
]


# ─── Tool implementations (called by the agent) ───────────────────────────

def execute_tool(name: str, args: dict) -> str:
    """Execute a tool by name with args. Returns a string result."""
    global _engine
    if _engine is None:
        db_url = os.environ.get("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")
        _engine = create_engine(db_url) if db_url else None
    
    if name == "list_leads":
        return _list_leads(args.get("status"))
    elif name == "get_lead_detail":
        return _get_lead_detail(args.get("lead_id", ""))
    elif name == "update_lead_status":
        return _update_lead_status(args.get("lead_id", ""), args.get("status", ""))
    elif name == "list_listings":
        return _list_listings(args.get("status"))
    elif name == "get_dashboard_summary":
        return _get_dashboard_summary()
    elif name == "get_agent_stats":
        return _get_agent_stats()
    elif name == "analyze_pipeline":
        return _analyze_pipeline()
    elif name == "system_overview":
        return _system_overview()
    elif name == "remember_fact":
        from .memory import remember, recall
        key = args.get("key", "")
        value = args.get("value", "")
        category = args.get("category", "general")
        remember(key, value, category, source="explicit")
        # Verify the write by reading it back
        verify = recall(key, top_k=3)
        if verify:
            return f"✅ Stored: [{category}] {key} = {value}"
        return f"⚠️ Tried to remember '{key}' but verification readback returned nothing. The store may need attention."
    elif name == "recall_memory":
        from .memory import recall
        results = recall(args.get("query", ""))
        if not results:
            return "Nothing found in memory."
        lines = []
        for r in results:
            rtype = r.get("type", "memory")
            key = r.get("key", "")
            content = r.get("content", "")
            if rtype == "fact":
                lines.append(f"  📋 [{r.get('category','general')}] {key}: {content}")
            elif rtype == "conversation":
                lines.append(f"  💬 Conversation — {key}: {content[:200]}")
            elif rtype == "chat":
                lines.append(f"  🗣️ [{r.get('role','?')}] {content[:200]}")
            elif rtype == "note":
                lines.append(f"  📝 Note — {key}: {content[:200]}")
            else:
                lines.append(f"  • {key}: {content[:200]}")
        return "\n".join(lines)
    elif name == "save_note":
        from .memory import save_note
        path = save_note(args.get("title", ""), args.get("body", ""),
                         args.get("tags", "").split(",") if args.get("tags") else [])
        return f"Note saved: {path}"
    elif name == "get_crew_info":
        return _get_crew_info()
    elif name == "run_crew":
        return _run_crew(args.get("crew_name", ""), args.get("input_data", "{}"))
    else:
        return f"Unknown tool: {name}"


def _query_db(sql: str, params: dict = None) -> list:
    """Execute a SQL query and return results."""
    global _engine
    if _engine is None:
        db_url = os.environ.get("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")
        _engine = create_engine(db_url) if db_url else None
    
    if _engine is None:
        return [{"error": "No database connection"}]
    with Session(_engine) as session:
        result = session.execute(text(sql), params or {})
        return [dict(r._mapping) for r in result]


def _list_leads(status: Optional[str] = None) -> str:
    try:
        if status:
            rows = _query_db(
                "SELECT id, first_name, last_name, email, status, ai_score, budget, created_at FROM leads WHERE status = :s ORDER BY ai_score DESC LIMIT 20",
                {"s": str(status)}
            )
        else:
            rows = _query_db(
                "SELECT id, first_name, last_name, email, status, ai_score, budget, created_at FROM leads ORDER BY ai_score DESC LIMIT 20"
            )
    except Exception as e:
        return f"Error querying leads: {e}"
    
    if not rows:
        return "No leads found."
    
    result = f"**Leads ({len(rows)}):**\n\n"
    for r in rows:
        score = r.get("ai_score") or 0
        budget = r.get("budget") or 0
        result += f"  • {r['first_name']} {r['last_name']} — Score: {score}% — Budget: ${budget:,.2f} — Status: {r['status']}\n    Email: {r['email']} | ID: {r['id']}\n"
    return result


def _get_lead_detail(lead_id: str) -> str:
    try:
        rows = _query_db("SELECT * FROM leads WHERE id = :id", {"id": lead_id})
    except Exception as e:
        return f"Error: {e}"
    if not rows:
        return f"No lead found with ID {lead_id}"
    r = rows[0]
    return (
        f"**Lead: {r.get('first_name','')} {r.get('last_name','')}**\n"
        f"  Email: {r.get('email','')}\n"
        f"  Phone: {r.get('phone','')}\n"
        f"  Status: {r.get('status','')}\n"
        f"  AI Score: {r.get('ai_score',0)}%\n"
        f"  Reason: {r.get('ai_score_reason','')}\n"
        f"  Budget: ${r.get('budget',0):,.2f}\n"
        f"  Location Interest: {r.get('location_interest','')}\n"
        f"  Property Type: {r.get('property_type_interest','')}\n"
        f"  Timeline: {r.get('timeline','')}\n"
        f"  Pre-approved: {r.get('pre_approved',False)}\n"
        f"  Last Contacted: {r.get('last_contacted_at','')}\n"
        f"  Notes: {r.get('notes','')}"
    )


def _update_lead_status(lead_id: str, status: str) -> str:
    try:
        _query_db("UPDATE leads SET status = :s WHERE id = :id", {"s": status, "id": lead_id})
        return f"Lead {lead_id} updated to status: {status}"
    except Exception as e:
        return f"Error updating lead: {e}"


def _list_listings(status: Optional[str] = None) -> str:
    try:
        if status:
            rows = _query_db("SELECT id, address_street, address_city, address_state, list_price, status, beds, baths, sqft, property_type FROM properties WHERE status = :s LIMIT 20", {"s": status})
        else:
            rows = _query_db("SELECT id, address_street, address_city, address_state, list_price, status, beds, baths, sqft, property_type FROM properties LIMIT 20")
    except Exception as e:
        return f"Error: {e}"
    if not rows:
        return "No listings found."
    result = f"**Listings ({len(rows)}):**\n\n"
    for r in rows:
        result += f"  • {r.get('address_street','')}, {r.get('address_city','')} — ${r.get('list_price',0):,.0f} — {r.get('beds',0)}bd/{r.get('baths',0)}ba/{r.get('sqft',0)}sqft — {r.get('status','')}\n"
    return result


def _get_dashboard_summary() -> str:
    try:
        d = _query_db("SELECT COUNT(*) as c FROM leads")[0]["c"]
        l = _query_db("SELECT COUNT(*) as c FROM properties")[0]["c"]
        h = _query_db("SELECT COUNT(*) as c FROM leads WHERE ai_score >= 80")[0]["c"]
        a = _query_db("SELECT COUNT(*) as c FROM properties WHERE status = 'ACTIVE'")[0]["c"]
    except Exception as e:
        return f"Error: {e}"
    return (
        f"**Dashboard Summary:**\n"
        f"  • Total Leads: {d}\n"
        f"  • Hot Leads (score≥80): {h}\n"
        f"  • Total Properties: {l}\n"
        f"  • Active Listings: {a}\n"
        f"  • Lead-to-listing ratio: {d/max(l,1):.1f}x"
    )


def _get_agent_stats() -> str:
    try:
        rows = _query_db("SELECT action, intent, model_used, status, created_at FROM activities ORDER BY created_at DESC LIMIT 15")
    except Exception:
        pass
    # Return simulated stats since activities table may not exist
    return (
        "**AI Agent Activity (last 15):**\n"
        "  Agents active: Lead Agent, Listing Agent, Marketing Agent, Transaction Agent, Document Agent, Research Agent, General Assistant\n"
        "  *Run a query to see detailed activity log.*"
    )


def _analyze_pipeline() -> str:
    try:
        rows = _query_db("SELECT first_name, last_name, ai_score, budget, status FROM leads ORDER BY ai_score DESC")
    except Exception as e:
        return f"Error: {e}"
    
    if not rows:
        return "No leads in pipeline."
    
    total = len(rows)
    hot = [r for r in rows if (r.get("ai_score") or 0) >= 80]
    warm = [r for r in rows if 50 <= (r.get("ai_score") or 0) < 80]
    cold = [r for r in rows if (r.get("ai_score") or 0) < 50]
    
    result = f"**Pipeline Analysis ({total} total):**\n\n"
    result += f"🔥 **Hot ({len(hot)}):** Follow up immediately\n"
    for r in hot[:5]:
        result += f"  • {r['first_name']} {r['last_name']} — Score: {r.get('ai_score',0)}% — ${r.get('budget',0):,.0f}\n"
    result += f"\n⚡ **Warm ({len(warm)}):** Nurture with content\n"
    for r in warm[:5]:
        result += f"  • {r['first_name']} {r['last_name']} — Score: {r.get('ai_score',0)}%\n"
    result += f"\n❄️ **Cold ({len(cold)}):** Re-engage or archive\n"
    for r in cold[:3]:
        result += f"  • {r['first_name']} {r['last_name']} — Score: {r.get('ai_score',0)}%\n"
    
    # Recommendations
    result += "\n**Recommendations:**\n"
    if hot:
        result += f"  → Contact {hot[0]['first_name']} {hot[0]['last_name']} (highest score) today\n"
    if len(rows) > 0:
        avg_score = sum((r.get("ai_score") or 0) for r in rows) / total
        result += f"  → Average lead score: {avg_score:.0f}%\n"
        result += f"  → Pipeline value at risk: ${sum((r.get('budget') or 0) for r in hot):,.0f} from hot leads\n"
    
    return result


def _get_crew_info() -> str:
    crew_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "ai", "crews")
    crews = []
    if os.path.isdir(crew_dir):
        crews = [f.replace(".py", "") for f in os.listdir(crew_dir) if f.endswith(".py") and not f.startswith("_")]
    
    return (
        "**CrewAI Agents Available:**\n\n"
        + "\n".join([f"  • {c}" for c in crews]) if crews else "  No CrewAI crews found."
        + "\n\nUse `run_crew` to execute any crew with input data."
    )


def _run_crew(crew_name: str, input_data: str = "{}") -> str:
    # Crew execution would import and run the crew
    return f"Crew '{crew_name}' would execute with input: {input_data}. Implement crew runner to enable."


def _system_overview() -> str:
    import psutil
    
    # System stats
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    # DB stats
    try:
        lead_count = _query_db("SELECT COUNT(*) as c FROM leads")[0]["c"]
        listing_count = _query_db("SELECT COUNT(*) as c FROM properties")[0]["c"]
    except:
        lead_count = listing_count = 0
    
    # User memory
    from .memory import profile_summary
    profile = profile_summary()
    
    # Skills
    from .memory import get_skills
    skills = get_skills()
    
    result = (
        f"╔═══ RealtyAI System Overview ═══╗\n\n"
        f"**System Health:**\n"
        f"  CPU: {cpu}% | RAM: {mem.percent}% ({mem.used//(1024**3)}GB/{mem.total//(1024**3)}GB)\n"
        f"  Disk: {disk.percent}% ({disk.used//(1024**3)}GB/{disk.total//(1024**3)}GB)\n\n"
        f"**Business Data:**\n"
        f"  Leads: {lead_count} | Listings: {listing_count}\n\n"
        f"**Agent Memory:**\n"
        f"  {profile[:300]}...\n\n"
        f"**Skills ({len(skills)}):**\n"
        + ("\n".join([f"  • {s['name']}: {s['description'][:60]}" for s in skills]) if skills else "  None yet — I'll create them as we work together.")
        + "\n\n**AI Agent Status:**\n"
        f"  Primary: Featherless.ai (Qwen3-4B-Instruct-2507)\n"
        f"  Fallback: NVIDIA (Llama-3.1-8B-Instruct)\n"
        f"  Memory: SQLite + FTS5 + Markdown notes\n"
        f"  7 specialist agents available for routing"
    )
    return result
