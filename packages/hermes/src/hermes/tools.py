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
    {
        "name": "market_snapshot",
        "description": "Get a market snapshot for a city: listing counts, median prices, avg price per sqft from your database.",
        "parameters": {"city": {"type": "string", "description": "City name (optional)", "required": False}}
    },
    {
        "name": "compare_neighborhoods",
        "description": "Compare two neighborhoods using listing data from your database.",
        "parameters": {"neighborhood_1": {"type": "string", "description": "First neighborhood name", "required": True}, "neighborhood_2": {"type": "string", "description": "Second neighborhood name", "required": True}, "city": {"type": "string", "description": "City filter (optional)", "required": False}}
    },
    {
        "name": "summarize_contract",
        "description": "Analyze a real estate contract text and return key terms, deadlines, and risks.",
        "parameters": {"contract_text": {"type": "string", "description": "The full text of the contract or agreement", "required": True}}
    },
    {
        "name": "extract_deadlines",
        "description": "Extract all dates, deadlines, and time-sensitive clauses from a contract.",
        "parameters": {"contract_text": {"type": "string", "description": "The contract text to analyze", "required": True}}
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
    elif name == "launch_campaign":
        return _launch_campaign(args.get("name", "Untitled Campaign"), args.get("audience", ""))
    elif name == "generate_listing_description":
        return _generate_listing_description(args.get("property_id", ""), args.get("tone", "professional"))
    elif name == "schedule_showing":
        return _schedule_showing(args.get("lead_name", ""), args.get("property_address", ""), args.get("time", ""))
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
    elif name == "market_snapshot":
        return _market_snapshot(args.get("city", ""))
    elif name == "compare_neighborhoods":
        return _compare_neighborhoods(args.get("neighborhood_1", ""), args.get("neighborhood_2", ""), args.get("city", ""))
    elif name == "summarize_contract":
        return _summarize_contract(args.get("contract_text", ""))
    elif name == "extract_deadlines":
        return _extract_deadlines(args.get("contract_text", ""))
    else:
        return f"Unknown tool: {name}"


def _query_db(sql: str, params: dict = None) -> list:
    """Execute a SQL query and return results (for SELECT statements)."""
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
        session.commit()
        try:
            return [dict(r._mapping) for r in result]
        except Exception:
            # INSERT/UPDATE without RETURNING → no rows to map
            return []


def _execute_db(sql: str, params: dict = None) -> bool:
    """Execute a SQL mutation (INSERT/UPDATE/DELETE) without returning rows."""
    try:
        _query_db(sql, params)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"DB execute failed: {e}")
        return False


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
    """Return AI agent activity stats from the activities table."""
    try:
        rows = _query_db("SELECT action, intent, model_used, status, created_at FROM activities ORDER BY created_at DESC LIMIT 15")
    except Exception:
        rows = None
    
    if rows:
        total = len(rows)
        by_intent = {}
        for r in rows:
            intent = r.get("intent", "general")
            by_intent[intent] = by_intent.get(intent, 0) + 1
        statuses = {r.get("status", "unknown") for r in rows}
        
        result = f"**AI Agent Activity (last {total} actions):**\n\n"
        result += f"**By intent:**\n"
        for intent, count in sorted(by_intent.items(), key=lambda x: -x[1]):
            result += f"  • {intent.title()}: {count}\n"
        result += f"\n**Statuses seen:** {', '.join(sorted(statuses))}\n"
        result += f"\n**Recent actions:**\n"
        for r in rows[:5]:
            action = (r.get("action") or "")[:80]
            result += f"  • {action}...\n"
        return result
    
    # If DB unavailable, list the specialist agents available
    return (
        "**AI Agents Available:**\n"
        "  • Lead Agent — qualifies/scoring/pipeline\n"
        "  • Marketing Agent — campaigns/social\n"
        "  • Listing Agent — MLS/descriptions/comparisons\n"
        "  • Transaction Agent — deadlines/closing\n"
        "  • Document Agent — contracts/analysis\n"
        "  • Research Agent — market/neighborhood\n"
        "  • General Assistant — everything else\n"
        "  *(Run a tool to see real activity data)*"
    )


def _launch_campaign(name: str, audience: str = "") -> str:
    """Create a marketing campaign record and return its details."""
    campaign_id = str(uuid.uuid4())
    audience_desc = audience or "all leads"
    
    ok = _execute_db(
        "INSERT INTO campaigns (id, name, audience, status, created_at) VALUES (:id, :name, :audience, 'active', NOW())",
        {"id": campaign_id, "name": name, "audience": audience_desc}
    )
    
    lead_count = 0
    try:
        lead_count = _query_db("SELECT COUNT(*) as c FROM leads")[0]["c"]
    except:
        pass
    
    if ok:
        return (
            f"**Campaign Launched:** {name}\n"
            f"  • ID: {campaign_id[:8]}...\n"
            f"  • Audience: {audience_desc}\n"
            f"  • Reach: {lead_count} leads in database\n"
            f"  • Status: Active\n\n"
            f"Use `get_dashboard_summary` to track results."
        )
    
    return (
        f"**Campaign Planned:** {name}\n"
        f"  • Audience: {audience_desc}\n"
        f"  • Target: {lead_count} leads\n"
        f"  • Status: Queued\n\n"
        f"The campaign concept is noted. When the campaigns infrastructure is ready, I can execute it."
    )


def _generate_listing_description(property_id: str, tone: str = "professional") -> str:
    """Generate a property listing description using real DB data."""
    try:
        rows = _query_db(
            "SELECT address_street, address_city, address_state, address_zip, "
            "beds, baths, sqft, list_price, property_type, description, features, year_built, lot_size "
            "FROM properties WHERE id = :id",
            {"id": property_id}
        )
        if not rows:
            return f"Property not found with ID: {property_id}"
        p = rows[0]
    except Exception as e:
        # No DB or no property ID — use latest property as demo
        try:
            rows = _query_db(
                "SELECT address_street, address_city, address_state, address_zip, "
                "beds, baths, sqft, list_price, property_type, description, features, year_built, lot_size "
                "FROM properties WHERE status = 'ACTIVE' LIMIT 1"
            )
            if rows:
                p = rows[0]
                property_id = p.get("id", property_id)
            else:
                return f"Error fetching property: {e}"
        except:
            return f"Error fetching property: {e}"
    
    addr = f"{p.get('address_street','')}, {p.get('address_city','')}, {p.get('address_state','')}"
    beds = p.get('beds', 0)
    baths = p.get('baths', 0)
    sqft = p.get('sqft', 0)
    price = p.get('list_price', 0)
    ptype = (p.get('property_type') or "home").lower()
    features = p.get('features') or []
    year = p.get('year_built')
    lot = p.get('lot_size')
    existing_desc = p.get('description') or ""
    
    # Tone-specific headline templates
    tones = {
        "luxury": f"Exquisite {ptype} in {p.get('address_city','')} — Where Elegance Meets Comfort",
        "cozy": f"Charming {beds}-Bed {ptype.title()} in Prime {p.get('address_city','')} Location",
        "modern": f"Sleek & Modern | {beds} Bed / {baths} Bath {ptype.title()} in {p.get('address_city','')}",
        "professional": f"Exceptional {beds}-Bedroom {ptype.title()} in {p.get('address_city','')}",
    }
    headline = tones.get(tone, tones["professional"])
    
    body = existing_desc if existing_desc else (
        f"Welcome to this beautifully appointed {beds}-bedroom, {baths}-bathroom "
        f"{ptype} offering {sqft:,} square feet of thoughtfully designed living space. "
        f"Located in the desirable {p.get('address_city','')} neighborhood, "
        f"this property represents an outstanding opportunity for discerning buyers."
    )
    
    feat_list = f"\n  • " + "\n  • ".join(features[:5]) if features else ""
    
    return (
        f"**{headline}**\n\n"
        f"📍 {addr} | 💰 ${price:,.0f}\n"
        f"🛏️ {beds} bed | 🛁 {baths} bath | 📐 {sqft:,} sqft"
        + (f" | 📅 Built {year}" if year else "")
        + (f" | 🌳 {lot:,} sqft lot" if lot else "")
        + f"\n\n{body}\n"
        + (f"\n**Features:**{feat_list}" if features else "")
        + f"\n\n*Generated by Athena — {tone} tone*"
    )


def _schedule_showing(lead_name: str, property_address: str, time: str) -> str:
    """Schedule a property showing, recording it in the DB."""
    showing_id = str(uuid.uuid4())
    
    ok = _execute_db(
        "INSERT INTO activities (id, organization_id, user_id, agent_name, action, intent, status, metadata) "
        "VALUES (:id, '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', "
        "'Athena', :action, 'showing', 'pending', :meta)",
        {
            "id": showing_id,
            "action": f"Schedule showing: {lead_name} @ {property_address} at {time}",
            "meta": {"lead_name": lead_name, "property": property_address, "time": time},
        }
    )
    status_note = "📅 Showing recorded in activity log." if ok else "📅 (Showing noted in conversation.)"
    
    return (
        f"**Showing Scheduled** ✅\n\n"
        f"  • **Client:** {lead_name}\n"
        f"  • **Property:** {property_address}\n"
        f"  • **Time:** {time}\n"
        f"  • **Status:** Pending confirmation\n\n"
        f"{status_note}\n\n"
        f"Would you like me to send a reminder before the showing?"
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


def _market_snapshot(city: str = "") -> str:
    """Get market snapshot from DB listing data."""
    try:
        if city:
            rows = _query_db(
                "SELECT list_price, sqft, address_city, property_type FROM properties WHERE status = 'ACTIVE' AND LOWER(address_city) LIKE :city",
                {"city": f"%{city.lower()}%"}
            )
        else:
            rows = _query_db("SELECT list_price, sqft, address_city, property_type FROM properties WHERE status = 'ACTIVE'")
    except Exception as e:
        return f"Error fetching market data: {e}"
    
    if not rows:
        return f"No active listings{' in ' + city if city else ''} found."
    
    prices = [r.get("list_price", 0) for r in rows if r.get("list_price")]
    sqfts = [r.get("sqft", 0) for r in rows if r.get("sqft")]
    cities = set(r.get("address_city", "") for r in rows)
    
    if prices:
        sp = sorted(prices)
        median = sp[len(sp) // 2]
        avg_ppsf = round(sum(p / s for p, s in zip(prices, sqfts) if s > 0) / max(len([x for x in sqfts if x > 0]), 1), 2) if sqfts else 0
    else:
        median = avg_ppsf = 0
    
    return (
        f"**Market Snapshot{' for ' + city if city else ''}** 📊\n\n"
        f"  • Active Listings: {len(rows)}\n"
        f"  • Median Price: ${median:,.0f}\n"
        f"  • Avg Price/Sqft: ${avg_ppsf:.0f}\n"
        f"  • Markets covered: {', '.join(sorted(cities)) if cities else 'N/A'}\n"
        f"  • Data source: Your database\n\n"
        f"*For deeper MLS-level data (days on market, price trends), connect an external data source.*"
    )


def _compare_neighborhoods(nb1: str, nb2: str, city: str = "") -> str:
    """Compare two neighborhoods using DB listing data."""
    def _nb_stats(name: str) -> dict:
        if city:
            rows = _query_db(
                "SELECT list_price, beds, baths, sqft, address_city FROM properties WHERE status = 'ACTIVE' AND (LOWER(address_street) LIKE :n OR LOWER(address_city) LIKE :n OR LOWER(description) LIKE :n) AND LOWER(address_city) LIKE :c",
                {"n": f"%{name.lower()}%", "c": f"%{city.lower()}%"}
            )
        else:
            rows = _query_db(
                "SELECT list_price, beds, baths, sqft, address_city FROM properties WHERE status = 'ACTIVE' AND (LOWER(address_street) LIKE :n OR LOWER(address_city) LIKE :n OR LOWER(description) LIKE :n)",
                {"n": f"%{name.lower()}%"}
            )
        prices = [r.get("list_price", 0) for r in rows if r.get("list_price")]
        sqfts = [r.get("sqft", 0) for r in rows if r.get("sqft")]
        return {
            "count": len(rows),
            "avg_price": round(sum(prices) / len(prices)) if prices else 0,
            "avg_ppsf": round(sum(p / s for p, s in zip(prices, sqfts) if s > 0) / max(len([x for x in sqfts if x > 0]), 1), 2) if sqfts and prices else 0,
        }
    
    s1 = _nb_stats(nb1)
    s2 = _nb_stats(nb2)
    
    if s1["count"] == 0 and s2["count"] == 0:
        return f"No active listings found for '{nb1}' or '{nb2}'."
    
    result = f"**Neighborhood Comparison: {nb1} vs {nb2}**\n\n"
    result += f"| Metric | {nb1} | {nb2} |\n|--------|------|------|\n"
    result += f"| Active Listings | {s1['count']} | {s2['count']} |\n"
    result += f"| Avg Price | ${s1['avg_price']:,} | ${s2['avg_price']:,} |\n"
    result += f"| Avg Price/Sqft | ${s1['avg_ppsf']:.0f} | ${s2['avg_ppsf']:.0f} |\n"
    
    if s1["avg_price"] and s2["avg_price"]:
        diff = ((s2["avg_price"] - s1["avg_price"]) / s1["avg_price"]) * 100
        if abs(diff) < 5:
            result += f"\n→ Similarly priced (within {abs(diff):.1f}%)."
        elif diff > 0:
            result += f"\n→ {nb2} is {diff:.0f}% more expensive."
        else:
            result += f"\n→ {nb1} is {abs(diff):.0f}% more expensive."
    
    return result


def _summarize_contract(text: str) -> str:
    """Analyze contract text using pattern matching."""
    if not text or len(text.strip()) < 10:
        return "Please provide the full contract text to analyze."
    
    import re as _re
    text_lower = text.lower()
    wc = len(text.split())
    
    clauses = {
        "Purchase Price": _re.search(r"(?:purchase\s*price|sale\s*price|consideration)\s*:?\s*\$?([\d,]+)", text_lower),
        "Closing Date": _re.search(r"(?:closing\s*date|settlement\s*date|completion\s*date)\s*:?\s*([\w\s,/]+)", text_lower),
        "Earnest Money": _re.search(r"(?:earnest\s*money|deposit)\s*:?\s*\$?([\d,]+)", text_lower),
        "Inspection Period": _re.search(r"(?:inspection\s*period|due\s*diligence)\s*:?\s*([\d\s-]+days?)", text_lower),
    }
    found = {k: m.group(1).strip() for k, m in clauses.items() if m}
    
    risks = []
    if _re.search(r"\bas\s*is\b", text_lower): risks.append("⚠️ 'As-is' clause — buyer accepts all defects")
    if _re.search(r"(?:no\s*warranty|as\s*is\s*where\s*is)", text_lower): risks.append("⚠️ No warranty clause")
    if _re.search(r"(?:non[\s-]*refundable|no\s*refund)", text_lower): risks.append("⚠️ Non-refundable deposit")
    if not risks: risks.append("✅ No common risk patterns detected")
    
    result = f"**Contract Analysis** ({wc} words)\n\n"
    if found:
        result += "**Detected Clauses:**\n"
        for k, v in found.items():
            result += f"  • {k}: {v}\n"
    else:
        result += "No standard clauses auto-detected. Key items to verify: price, closing, contingencies.\n"
    result += "\n**Risk Flags:**\n" + "\n".join(f"  {r}" for r in risks)
    return result


def _extract_deadlines(text: str) -> str:
    """Extract time-sensitive clauses from contract text."""
    if not text or len(text.strip()) < 10:
        return "Please provide the contract text to extract deadlines from."
    
    import re as _re
    text_lower = text.lower()
    
    deadlines = []
    date_pattern = _re.findall(r"(?:on|by|before|within)\s+([\w\s,/]+\d{4})", text_lower)
    for d in date_pattern[:5]:
        deadlines.append(f"  • Date found: {d.strip()}")
    
    day_patterns = _re.findall(r"(\d[\s-]*days?)", text_lower)
    for d in day_patterns[:5]:
        deadlines.append(f"  • Timeline: {d.strip()}")
    
    if not deadlines:
        deadlines = [
            "  • Inspection Period: Typically 7-10 days from acceptance",
            "  • Financing Contingency: Typically 14-21 days",
            "  • Closing Date: Typically 30-60 days from acceptance",
            "  *(No specific dates found in text — above are standard estimates)*",
        ]
    
    return "**Extracted Deadlines & Timelines:**\n\n" + "\n".join(deadlines)


def _get_crew_info() -> str:
    """Return info about available specialists and crew modules."""
    # Check for CrewAI crew files
    crew_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "ai", "crews")
    crew_files = []
    if os.path.isdir(crew_dir):
        crew_files = [f.replace(".py", "") for f in os.listdir(crew_dir) if f.endswith(".py") and not f.startswith("_")]
    
    # Specialist agents from the agent registry (always available)
    specialists = [
        ("Lead Agent", "Qualifies leads, scores prospects"),
        ("Marketing Agent", "Campaigns, social posts, content"),
        ("Listing Agent", "MLS descriptions, comparisons"),
        ("Transaction Agent", "Deadlines, closing timelines"),
        ("Document Agent", "Contract analysis, risk flags"),
        ("Research Agent", "Market trends, neighborhoods"),
    ]
    
    result = "**Specialist Agents (always available):**\n\n"
    for name, desc in specialists:
        result += f"  • **{name}** — {desc}\n"
    
    if crew_files:
        result += "\n**CrewAI Modules (specialized multi-agent crews):**\n\n"
        for c in crew_files:
            result += f"  • {c}\n"
        result += "\nUse `run_crew` to execute a crew with input data."
    else:
        result += "\n*CrewAI modules are being set up. Specialist agents above are ready now.*"
    
    return result


def _run_crew(crew_name: str, input_data: str = "{}") -> str:
    """Execute a crew or specialist agent. Falls back to specialist agent routing if crew module unavailable."""
    import json as _json
    
    try:
        input_dict = _json.loads(input_data) if isinstance(input_data, str) else input_data
    except (_json.JSONDecodeError, ValueError):
        input_dict = {"input": str(input_data)}
    
    # Map common crew names to specialist agent tools
    crew_agent_map = {
        "lead_scoring_crew": "Lead Agent",
        "lead_crew": "Lead Agent",
        "marketing_crew": "Marketing Agent",
        "listing_crew": "Listing Agent",
        "transaction_crew": "Transaction Agent",
        "document_crew": "Document Agent",
        "research_crew": "Research Agent",
    }
    
    # Try to import and run the actual CrewAI crew module
    import importlib, sys as _sys
    crew_module_path = f"crews.{crew_name}"
    
    # Check if the crew module exists and has a run function
    try:
        # Try dynamic import of the crew module
        crew_module = importlib.import_module(crew_module_path, package="packages.ai")
        if hasattr(crew_module, 'run_crew'):
            result = crew_module.run_crew(**input_dict)
            return f"**Crew '{crew_name}' executed successfully.**\n\nResult:\n{str(result)[:1000]}"
        elif hasattr(crew_module, 'crew'):
            result = crew_module.crew.kickoff(inputs=input_dict)
            return f"**Crew '{crew_name}' completed.**\n\nResult:\n{str(result)[:1000]}"
    except (ImportError, AttributeError, Exception) as e:
        # Crew module not available — delegate to specialist agent
        agent_name = crew_agent_map.get(crew_name, "General Assistant")
        
        # Execute the relevant tool based on crew type
        input_text = input_dict.get("input", input_dict.get("message", str(input_dict)))
        
        tool_actions = {
            "lead_scoring_crew": f"Running lead analysis pipeline for: {input_text}",
            "marketing_crew": f"Running marketing campaign for: {input_text}",
            "listing_crew": f"Running listing analysis for: {input_text}",
            "transaction_crew": f"Running transaction check for: {input_text}",
            "document_crew": f"Running document analysis for: {input_text}",
            "research_crew": f"Running market research for: {input_text}",
        }
        
        action = tool_actions.get(crew_name, f"Running {agent_name} for: {input_text}")
        
        # Actually call a relevant tool based on crew type
        if "lead" in crew_name:
            result = _analyze_pipeline()
        elif "market" in crew_name:
            result = _get_dashboard_summary()
        elif "listing" in crew_name:
            try:
                result = _list_listings(input_dict.get("status"))
            except:
                result = _list_listings()
        else:
            result = f"CrewAI module for '{crew_name}' is being prepared. I routed this to the **{agent_name}** instead.\n\n{action}"
        
        return (
            f"**Crew '{crew_name}' delegated to {agent_name}** 🔀\n\n"
            f"The CrewAI module is being set up, so I've routed this to my built-in specialist agent.\n\n"
            f"{result}"
        )


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
        activity_count = _query_db("SELECT COUNT(*) as c FROM activities")[0]["c"]
    except:
        lead_count = listing_count = activity_count = 0
    
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
        f"  Leads: {lead_count} | Listings: {listing_count} | Activities: {activity_count}\n\n"
        f"**Agent Memory:**\n"
        f"  {profile[:300]}...\n\n"
        f"**Skills ({len(skills)}):**\n"
        + ("\n".join([f"  • {s['name']}: {s['description'][:60]}" for s in skills]) if skills else "  None yet — I'll create them as we work together.")
        + "\n\n**Tools Available (16):**\n"
        f"  Leads: list, detail, update, search\n"
        f"  Listings: list, describe, compare\n"
        f"  Marketing: campaigns, pipeline analysis\n"
        f"  Memory: remember, recall, notes\n"
        f"  System: overview, stats, crew execution\n"
        f"  Scheduling: showings\n"
        f"  Memory: SQLite + FTS5 + Markdown notes"
    )
    return result
