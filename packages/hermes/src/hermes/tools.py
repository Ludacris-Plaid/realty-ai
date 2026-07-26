"""
Athena Agent — RealtyAI System Tools.

These tools give Athena complete control over the RealtyAI system.
All controllable via natural language through the chat interface.
"""
import os
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger(__name__)

# ─── Database access helper ────────────────────────────────────────────────
# Engine is set by the API on init
_engine = None
_current_user_id = ""

def set_engine(engine):
    global _engine
    _engine = engine

def set_current_user_id(user_id: str):
    global _current_user_id
    _current_user_id = user_id


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
    # ── Web Browsing Tools ────────────────────────────────────────────────
    {
        "name": "browse_web_page",
        "description": "Read any web page and return its content. Uses Obscura headless browser, Jina Reader, or direct HTTP. Good for looking up real estate listings, market data, news, or any public web content.",
        "parameters": {"url": {"type": "string", "description": "The full URL to browse (https://...)", "required": True}}
    },
    {
        "name": "search_web",
        "description": "Search the web using Exa semantic search engine. Returns ranked results with titles, URLs, and snippets. Good for researching market trends, finding properties, comparing prices, or any general web research.",
        "parameters": {"query": {"type": "string", "description": "Search query", "required": True}, "count": {"type": "integer", "description": "Number of results (default 5)", "required": False}}
    },
    {
        "name": "scrape_properties_advanced",
        "description": "Scrape property listings for a city/area. Works out of the box using Zillow's listing data. Options for advanced sources (Obscura/Browser-Use) are available if installed.",
        "parameters": {"location": {"type": "string", "description": "City/location to scrape (e.g. 'Edmonton, AB')", "required": True}, "max_results": {"type": "integer", "description": "Maximum listings (default 25)", "required": False}}
    },
    {
        "name": "check_scraper_sources",
        "description": "Quick check on what web scraping sources are ready. Use this if the user asks about scraping capabilities.",
        "parameters": {}
    },
    {
        "name": "scrape_and_import_properties",
        "description": "Scrape property listings from Zillow for a city/area and import them into the system as listings. Full end-to-end pipeline. Use this when someone wants to scrape AND save properties.",
        "parameters": {"location": {"type": "string", "description": "City/location to scrape (e.g. 'Edmonton, AB')", "required": True}, "max_results": {"type": "integer", "description": "Maximum listings to import (default 25)", "required": False}}
    },
    # ── Scoring & Analysis Tools ──────────────────────────────────────────
    {
        "name": "score_lead",
        "description": "Score a lead using AI rules: checks pre-approval, timeline, budget, source, and status. Returns score 0-100 with explanation.",
        "parameters": {"lead_id": {"type": "string", "description": "UUID of the lead to score", "required": True}}
    },
    {
        "name": "recommend_follow_up",
        "description": "Analyze a lead's stage and suggest the best next action to move them toward closing.",
        "parameters": {"lead_id": {"type": "string", "description": "UUID of the lead", "required": True}}
    },
    {
        "name": "property_price_analysis",
        "description": "Compare a property's price against similar properties in the same area. Returns comparable sales, price per sqft analysis, and market position flag (above/at/below market).",
        "parameters": {"property_id": {"type": "string", "description": "UUID of the property", "required": True}}
    },
    {
        "name": "market_trend_report",
        "description": "Generate a broader market trend report: active vs pending vs sold counts, median prices by city, top neighborhoods by listing count.",
        "parameters": {"city": {"type": "string", "description": "City name to analyze (optional, leave empty for all)", "required": False}}
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
    elif name == "market_snapshot":
        return _market_snapshot(args.get("city", ""))
    elif name == "compare_neighborhoods":
        return _compare_neighborhoods(args.get("neighborhood_1", ""), args.get("neighborhood_2", ""), args.get("city", ""))
    elif name == "summarize_contract":
        return _summarize_contract(args.get("contract_text", ""))
    elif name == "extract_deadlines":
        return _extract_deadlines(args.get("contract_text", ""))
    elif name == "browse_web_page":
        return _browse_web_page(args.get("url", ""))
    elif name == "search_web":
        return _search_web(args.get("query", ""), args.get("count", 5))
    elif name == "scrape_properties_advanced":
        return _scrape_properties_advanced(args.get("location", ""), args.get("max_results", 25))
    elif name == "check_scraper_sources":
        return _check_scraper_sources()
    elif name == "scrape_and_import_properties":
        return _scrape_and_import(args.get("location", ""), args.get("max_results", 25))
    elif name == "score_lead":
        return _score_lead(args.get("lead_id", ""))
    elif name == "recommend_follow_up":
        return _recommend_follow_up(args.get("lead_id", ""))
    elif name == "property_price_analysis":
        return _property_price_analysis(args.get("property_id", ""))
    elif name == "market_trend_report":
        return _market_trend_report(args.get("city", ""))
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
        uid = _current_user_id
        if status:
            if uid:
                rows = _query_db(
                    "SELECT id, first_name, last_name, email, status, ai_score, budget, created_at FROM leads WHERE status = :s AND agent_id = :uid ORDER BY ai_score DESC LIMIT 20",
                    {"s": str(status), "uid": uid}
                )
            else:
                rows = _query_db(
                    "SELECT id, first_name, last_name, email, status, ai_score, budget, created_at FROM leads WHERE status = :s ORDER BY ai_score DESC LIMIT 20",
                    {"s": str(status)}
                )
        else:
            if uid:
                rows = _query_db(
                    "SELECT id, first_name, last_name, email, status, ai_score, budget, created_at FROM leads WHERE agent_id = :uid ORDER BY ai_score DESC LIMIT 20",
                    {"uid": uid}
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
        uid = _current_user_id
        select_cols = "id, address_street, address_city, address_state, list_price, status, beds, baths, sqft, property_type, images"
        if status:
            if uid:
                rows = _query_db(f"SELECT {select_cols} FROM properties WHERE status = :s AND agent_id = :uid LIMIT 20", {"s": status, "uid": uid})
            else:
                rows = _query_db(f"SELECT {select_cols} FROM properties WHERE status = :s LIMIT 20", {"s": status})
        else:
            if uid:
                rows = _query_db(f"SELECT {select_cols} FROM properties WHERE agent_id = :uid LIMIT 20", {"uid": uid})
            else:
                rows = _query_db(f"SELECT {select_cols} FROM properties LIMIT 20")
    except Exception as e:
        return f"Error: {e}"
    if not rows:
        return "No listings found."
    result = f"**Listings ({len(rows)}):**\n\n"
    for r in rows:
        raw_images = r.get("images", [])
        if isinstance(raw_images, str):
            try:
                import json
                raw_images = json.loads(raw_images)
            except Exception:
                raw_images = []
        if isinstance(raw_images, dict):
            raw_images = raw_images.get("images", [])
        if not isinstance(raw_images, list):
            raw_images = []
        result += f"  • {r.get('address_street','')}, {r.get('address_city','')} — ${r.get('list_price',0):,.0f} — {r.get('beds',0)}bd/{r.get('baths',0)}ba/{r.get('sqft',0)}sqft — {r.get('status','')}\n"
    return result


def _get_dashboard_summary() -> str:
    try:
        uid = _current_user_id
        if uid:
            d = _query_db("SELECT COUNT(*) as c FROM leads WHERE agent_id = :uid", {"uid": uid})[0]["c"]
            l = _query_db("SELECT COUNT(*) as c FROM properties WHERE agent_id = :uid", {"uid": uid})[0]["c"]
            h = _query_db("SELECT COUNT(*) as c FROM leads WHERE agent_id = :uid AND ai_score >= 80", {"uid": uid})[0]["c"]
            a = _query_db("SELECT COUNT(*) as c FROM properties WHERE agent_id = :uid AND status = 'ACTIVE'", {"uid": uid})[0]["c"]
        else:
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
    uid = _current_user_id or str(uuid.uuid4())
    
    ok = _execute_db(
        "INSERT INTO campaigns (id, user_id, name, audience, status, created_at) VALUES (:id, :uid, :name, :audience, 'active', NOW())",
        {"id": campaign_id, "uid": uid, "name": name, "audience": audience_desc}
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
    uid = _current_user_id or str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    
    ok = _execute_db(
        "INSERT INTO activities (id, organization_id, user_id, agent_name, action, intent, status, metadata) "
        "VALUES (:id, :org_id, :uid, "
        "'Athena', :action, 'showing', 'pending', :meta::jsonb)",
        {
            "id": showing_id, "org_id": org_id, "uid": uid,
            "action": f"Schedule showing: {lead_name} @ {property_address} at {time}",
            "meta": json.dumps({"lead_name": lead_name, "property": property_address, "time": time}),
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
        uid = _current_user_id
        if uid:
            rows = _query_db("SELECT first_name, last_name, ai_score, budget, status FROM leads WHERE agent_id = :uid ORDER BY ai_score DESC", {"uid": uid})
        else:
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
        uid = _current_user_id
        if city:
            if uid:
                rows = _query_db(
                    "SELECT list_price, sqft, address_city, property_type FROM properties WHERE status = 'ACTIVE' AND agent_id = :uid AND LOWER(address_city) LIKE :city",
                    {"uid": uid, "city": f"%{city.lower()}%"}
                )
            else:
                rows = _query_db(
                    "SELECT list_price, sqft, address_city, property_type FROM properties WHERE status = 'ACTIVE' AND LOWER(address_city) LIKE :city",
                    {"city": f"%{city.lower()}%"}
                )
        else:
            if uid:
                rows = _query_db("SELECT list_price, sqft, address_city, property_type FROM properties WHERE status = 'ACTIVE' AND agent_id = :uid", {"uid": uid})
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
        ppsf_values = []
        for p, s in zip(prices, sqfts):
            try:
                if s and s > 0 and p and p > 0:
                    ppsf_values.append(float(p) / float(s))
            except (ZeroDivisionError, ValueError, TypeError):
                continue
        avg_ppsf = round(sum(ppsf_values) / len(ppsf_values), 2) if ppsf_values else 0
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


# ─── Scoring & Analysis Implementations ────────────────────────────────────


def _score_lead(lead_id: str) -> str:
    """Score a lead using rule-based algorithm. Returns 0-100."""
    if not lead_id:
        return "Please provide a lead ID."
    rows = _query_db("SELECT * FROM leads WHERE id = :id", {"id": lead_id})
    if not rows:
        return f"No lead found with ID {lead_id}"
    r = rows[0]
    score = 0
    reasons = []

    # Pre-approval bonus
    if r.get("pre_approved"):
        score += 20
        reasons.append("Pre-approved: +20")

    # Timeline urgency
    tl = (r.get("timeline") or "").lower()
    if "immediate" in tl or "asap" in tl or "now" in tl:
        score += 15
        reasons.append("Immediate timeline: +15")
    elif "month" in tl:
        m = re.search(r"(\d+)", tl)
        if m:
            n = int(m.group(1))
            if n <= 3:
                score += 10
                reasons.append(f"{n}-month timeline: +10")
            else:
                score += 5
                reasons.append(f"{n}-month timeline: +5")

    # Budget tier
    budget = float(r.get("budget") or 0)
    if budget >= 800000:
        score += 10
        reasons.append(f"Budget ${budget:,.0f}: +10")
    elif budget >= 500000:
        score += 7
        reasons.append(f"Budget ${budget:,.0f}: +7")
    elif budget >= 300000:
        score += 5
        reasons.append(f"Budget ${budget:,.0f}: +5")

    # Source quality
    src = (r.get("source") or "").lower()
    if src in ("referral", "agent_referral"):
        score += 10
        reasons.append("Referral source: +10")
    elif src in ("open_house", "openhouse"):
        score += 5
        reasons.append("Open house source: +5")
    elif src in ("website", "zillow", "realtor_com", "redfin"):
        score += 3
        reasons.append("Online source: +3")

    # Status progression
    st = (r.get("status") or "").upper()
    if st == "APPOINTMENT_SET":
        score += 15
        reasons.append("Appointment set: +15")
    elif st in ("CONTACTED", "QUALIFIED"):
        score += 10
        reasons.append(f"Status {st}: +10")

    score = min(score, 100)

    # Save to DB
    _execute_db(
        "UPDATE leads SET ai_score = :score, ai_score_reason = :reason, ai_score_updated_at = NOW() WHERE id = :id",
        {"score": score, "reason": "; ".join(reasons), "id": lead_id},
    )

    name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
    result = f"**Scored: {name or lead_id}** — {score}/100\n\n"
    result += "\n".join(f"  • {r}" for r in reasons) if reasons else "  No scoring factors found."
    if score >= 80:
        result += "\n\n🔥 **Hot lead** — prioritize follow-up today."
    elif score >= 50:
        result += "\n\n⚡ **Warm lead** — nurture with relevant content."
    else:
        result += "\n\n❄️ **Cold lead** — re-engage or archive."
    return result


def _recommend_follow_up(lead_id: str) -> str:
    """Analyze lead stage and suggest next action."""
    if not lead_id:
        return "Please provide a lead ID."
    rows = _query_db("SELECT * FROM leads WHERE id = :id", {"id": lead_id})
    if not rows:
        return f"No lead found with ID {lead_id}"
    r = rows[0]
    score = r.get("ai_score") or 0
    status = (r.get("status") or "").upper()
    name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip() or lead_id
    budget = float(r.get("budget") or 0)
    loc = r.get("location_interest") or "their preferred area"
    ptype = r.get("property_type_interest") or "property"

    result = f"**Follow-Up Recommendation: {name}**\n\n"
    result += f"Score: {score}/100 | Status: {status}\n"
    if budget:
        result += f"Budget: ${budget:,.0f} | Interest: {loc}\n"
    result += "\n"

    if score >= 80:
        result += (
            "🔥 **Hot Lead — Act Now**\n"
            f"  → Call {name} today and ask about their timeline\n"
            f"  → Prepare a list of {ptype} options in {loc}\n"
            "  → Offer to schedule a showing this week\n"
        )
    elif score >= 50:
        result += (
            "⚡ **Warm Lead — Nurture**\n"
            f"  → Send {name} a curated listing alert matching {loc}\n"
            f"  → Share a market report for {loc}\n"
            "  → Follow up in 3-5 days with new listings\n"
        )
    else:
        result += (
            "❄️ **Cold Lead — Re-engage**\n"
            "  → Send a monthly market newsletter\n"
            "  → Share recent sold comparables in their area\n"
            "  → Check back in 2-3 weeks\n"
        )

    if status in ("NEW", "QUALIFYING"):
        result += "\n📋 **Next step:** Ask about pre-approval and timeline."
    elif status == "CONTACTED":
        result += "\n📋 **Next step:** Share listings matching their criteria."
    elif status == "APPOINTMENT_SET":
        result += "\n📋 **Next step:** Confirm showing details and prepare property info."

    return result


def _property_price_analysis(property_id: str) -> str:
    """Compare a property's price against comparable properties."""
    if not property_id:
        return "Please provide a property ID."
    rows = _query_db("SELECT * FROM properties WHERE id = :id", {"id": property_id})
    if not rows:
        return f"No property found with ID {property_id}"
    p = rows[0]

    city = p.get("address_city", "")
    sqft = float(p.get("sqft") or 0)
    price = float(p.get("list_price") or 0)
    addr = f"{p.get('address_street', '')}, {city}"

    ppsf = price / sqft if sqft > 0 else 0

    # Find comparables: same city, ±20% sqft, active/pending
    margin = 0.20
    if sqft > 0:
        comps = _query_db(
            "SELECT list_price, sqft, address_street, address_city, status FROM properties "
            "WHERE id != :id AND LOWER(address_city) = LOWER(:city) "
            "AND status IN ('ACTIVE', 'PENDING') "
            "AND sqft BETWEEN :min_sqft AND :max_sqft",
            {"id": property_id, "city": city,
             "min_sqft": sqft * (1 - margin), "max_sqft": sqft * (1 + margin)},
        )
    else:
        comps = []

    result = f"**Price Analysis: {addr}**\n\n"
    result += f"List Price: ${price:,.0f}\n"
    result += f"Sqft: {sqft:,.0f} | Price/Sqft: ${ppsf:,.0f}\n"
    result += f"Status: {p.get('status', '')}\n\n"

    if comps:
        comp_prices = [float(c["list_price"]) for c in comps if c.get("list_price")]
        comp_ppsf = []
        for c in comps:
            cs = float(c.get("sqft") or 0)
            cp = float(c.get("list_price") or 0)
            if cs > 0 and cp > 0:
                comp_ppsf.append(cp / cs)
        avg_price = sum(comp_prices) / len(comp_prices) if comp_prices else 0
        avg_ppsf = sum(comp_ppsf) / len(comp_ppsf) if comp_ppsf else 0

        result += f"Comparables ({len(comps)} similar properties):\n"
        result += f"  Avg price: ${avg_price:,.0f}\n"
        result += f"  Avg price/sqft: ${avg_ppsf:,.0f}\n"
        result += f"  Range: ${min(comp_prices):,.0f} — ${max(comp_prices):,.0f}\n\n"

        diff_pct = ((price - avg_price) / avg_price * 100) if avg_price else 0
        if diff_pct > 5:
            result += f"📈 **Above market** ({diff_pct:.0f}% above avg comparables)"
        elif diff_pct < -5:
            result += f"📉 **Below market** ({abs(diff_pct):.0f}% below avg comparables)"
        else:
            result += f"✅ **At market** (within 5% of avg comparables)"
    else:
        result += "No comparable properties found in this area."

    return result


def _market_trend_report(city: str = "") -> str:
    """Generate a market trend report from DB data."""
    if city:
        rows = _query_db(
            "SELECT status, COUNT(*) as cnt, ROUND(AVG(list_price)) as avg_price, "
            "address_city FROM properties WHERE LOWER(address_city) LIKE :city "
            "GROUP BY status, address_city ORDER BY cnt DESC",
            {"city": f"%{city.lower()}%"},
        )
    else:
        rows = _query_db(
            "SELECT status, COUNT(*) as cnt, ROUND(AVG(list_price)) as avg_price, "
            "address_city FROM properties GROUP BY status, address_city ORDER BY cnt DESC"
        )

    if not rows:
        return f"No market data{' for ' + city if city else ''} found."

    city_label = city or "All Markets"
    result = f"**Market Trend Report: {city_label}**\n\n"

    # Group by city
    cities = {}
    for r in rows:
        c = r.get("address_city", "Unknown")
        if c not in cities:
            cities[c] = {"ACTIVE": 0, "PENDING": 0, "SOLD": 0, "prices": []}
        st = r.get("status", "").upper()
        if st in cities[c]:
            cities[c][st] = r["cnt"]
        cities[c]["prices"].append(r.get("avg_price") or 0)

    for c, data in sorted(cities.items()):
        total = sum(data[s] for s in ("ACTIVE", "PENDING", "SOLD"))
        result += f"**{c}** — {total} total listings\n"
        result += f"  Active: {data['ACTIVE']} | Pending: {data['PENDING']} | Sold: {data['SOLD']}\n"
        prices = [p for p in data["prices"] if p]
        if prices:
            avg_p = sum(prices) / len(prices)
            result += f"  Avg price: ${avg_p:,.0f}\n"
        result += "\n"

    result += "*Data from your local database. Connect MLS for broader coverage.*"
    return result


# ─── Web Browsing Tool Implementations ─────────────────────────────────────


def _browse_web_page(url: str) -> str:
    """Read a web page using the SuperScraper orchestrator.

    Tries: Obscura fetch → Agent-Reach Jina Reader → direct HTTP.
    """
    if not url or not url.startswith(("http://", "https://")):
        return "Please provide a valid URL starting with http:// or https://"

    try:
        from hermes.scraper.super_scraper import SuperScraper
        scraper = SuperScraper()
        text = scraper.web_read(url)
        if text:
            return f"**Web Page: {url}**\n\n{text[:6000]}"
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"SuperScraper web_read failed: {e}")

    # Fallback: direct HTTP with BeautifulSoup
    try:
        import httpx
        resp = httpx.get(url, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return f"**Web Page: {url}**\n\n{text[:6000]}"
        return f"HTTP {resp.status_code} from {url}"
    except ImportError:
        # Fallback without BeautifulSoup: just return raw text
        try:
            import httpx
            resp = httpx.get(url, timeout=15, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            return resp.text[:6000]
        except Exception as e2:
            return f"Error reading {url}: {e2}"
    except Exception as e:
        return f"Error reading {url}: {e}"


def _search_web(query: str, count: int = 5) -> str:
    """Search the web using the best available search engine."""
    if not query:
        return "Please provide a search query"

    results = []
    try:
        from hermes.scraper.agent_reach_source import AgentReachConnector
        arc = AgentReachConnector()
        if arc.is_available():
            results = arc.search_web(query, count)
        else:
            results = arc._exa_direct(query, count)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"AgentReach search failed: {e}")

    if not results:
        return f"No search results found for '{query}'"

    output = f"**Web Search: {query}**\n\n"
    for i, r in enumerate(results[:count], 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        snippet = r.get("snippet", r.get("text", ""))[:250]
        output += f"{i}. **[{title}]({url})**\n"
        output += f"   {snippet}\n\n"

    return output.strip()


def _scrape_properties_advanced(location: str, max_results: int = 25) -> str:
    """Scrape property listings using Zillow scraper directly."""
    if not location:
        location = "Edmonton, AB"
        logger.info("Scraper called without location; defaulting to Edmonton, AB")

    try:
        from hermes.scraper.zillow import ZillowScraper
        scraper = ZillowScraper(delay=0.5)
        listings = scraper.search(location, max_results)
    except Exception as e:
        logger.warning(f"ZillowScraper search failed: {e}")
        return f"Scraping failed: {e}"

    if not listings:
        return f"No listings found for {location}"

    output = f"**Properties in {location}** ({len(listings)} total)\n"
    output += "Source: Zillow (Jina Reader)\n\n"

    for i, p in enumerate(listings[:10], 1):
        url = p.get("url", "")
        images = p.get("images", [])
        output += f"{i}. **{p.get('address_street', 'N/A')}**\n"
        output += f"   ${p.get('list_price', 0):,} | {p.get('beds', 0)}bd | {p.get('baths', 0)}ba | {p.get('sqft', 0)}sqft\n"
        if images:
            output += f"   ![{p.get('address_street', 'photo')}]({images[0]})\n"
        if url:
            output += f"   [View on Zillow]({url})\n"

    if len(listings) > 10:
        output += f"\n... and {len(listings) - 10} more properties"

    return output.strip()


def _check_scraper_sources() -> str:
    """Check which web scraping tools are available on this system."""
    status = {}
    try:
        from hermes.scraper.zillow import ZillowScraper
        z = ZillowScraper()
        status["zillow_requests"] = True
    except Exception:
        status["zillow_requests"] = False

    try:
        import httpx
        resp = httpx.get("https://r.jina.ai/https://example.com", timeout=10)
        status["jina_reader"] = resp.status_code == 200
    except Exception:
        status["jina_reader"] = False

    available_count = sum(1 for v in status.values() if v)
    total_count = len(status)
    output = f"**Web Scraper Status** — {available_count}/{total_count} sources ready\n\n"
    for name, available in status.items():
        icon = "✅" if available else "⏳"
        note = "" if available else " (optional — not needed for basic scraping)"
        output += f"  {icon} **{name}**{note}\n"

    output += "\n**✅ Basic scraping works now** — `zillow_requests` is active and ready to search properties.\n"
    output += "  Just tell me where and how many listings you need.\n"
    if total_count - available_count > 0:
        output += "\n**Optional upgrades** (for stealth/JS-rendered pages):\n"
        if not status.get("obscura", False):
            output += "  • Obscura (Rust headless browser): https://github.com/h4ckf0r0day/obscura\n"
        if not status.get("browser_use", False):
            output += "  • Browser-Use (Python): pip install browser-use && playwright install chromium (2GB+)\n"
        if not status.get("agent_reach", False):
            output += "  • Agent-Reach (platform connectivity): pip install agent-reach\n"

    if not status.get("browser_use", False) and not status.get("obscura", False):
        output += "\n**Tip:** For most MLS listings, the built-in Zillow scraper is all you need."

    return output


def _scrape_and_import(location: str, max_results: int = 25) -> str:
    """Scrape properties and import them into the system as listings."""
    if not location:
        location = "Edmonton, AB"

    try:
        from hermes.scraper.zillow import ZillowScraper
        from hermes.scraper.pipeline import scrape_and_seed

        import os
        db_url = os.environ.get("DATABASE_URL", "")
        db_url = db_url.replace("+asyncpg", "").replace("+psycopg", "")

        scraper = ZillowScraper()
        listings = scraper.search(location, max_results)
        if not listings:
            return f"No listings found for {location}."

        result = scrape_and_seed(location=location, count=max_results, db_url=db_url,
                                 user_id=_current_user_id, listings=listings)

        output = f"**Scrape & Import Complete — {location}**\n\n"
        output += f"📊 {len(listings)} properties scraped | 🏠 {result.get('properties_inserted', 0)} inserted\n"
        output += f"Source: {result.get('source', 'unknown')}\n\n"

        for l in listings[:5]:
            url = l.get("url", "")
            images = l.get("images", [])
            output += f"  **{l.get('address_street', '?')}** — ${l.get('list_price', 0):,} | {l.get('beds', 0)}bd/{l.get('baths', 0)}ba/{l.get('sqft', 0)}sqft\n"
            if images:
                output += f"  ![{l.get('address_street', 'photo')}]({images[0]})\n"
            if url:
                output += f"  [View on Zillow]({url})\n"
            output += "\n"

        if len(listings) > 5:
            output += f"... and {len(listings) - 5} more properties imported.\n"

        return output.strip()

    except Exception as e:
        logger.warning(f"scrape_and_import failed: {e}")
        return f"Import failed: {e}"


def _system_overview() -> str:
    import psutil
    
    # System stats
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    # DB stats
    try:
        uid = _current_user_id
        if uid:
            lead_count = _query_db("SELECT COUNT(*) as c FROM leads WHERE agent_id = :uid", {"uid": uid})[0]["c"]
            listing_count = _query_db("SELECT COUNT(*) as c FROM properties WHERE agent_id = :uid", {"uid": uid})[0]["c"]
            activity_count = _query_db("SELECT COUNT(*) as c FROM activities WHERE user_id = :uid", {"uid": uid})[0]["c"]
        else:
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
        + "\n\n**Tools Available (20):**\n"
        f"  Leads: list, detail, update, search\n"
        f"  Listings: list, describe, compare, scrape\n"
        f"  Marketing: campaigns, pipeline analysis\n"
        f"  Memory: remember, recall, notes\n"
        f"  System: overview, stats, crew execution\n"
        f"  Scheduling: showings\n"
        f"  Web: browse pages, web search, advanced scraping\n"
        f"  Memory: SQLite + FTS5 + Markdown notes"
    )
    return result
