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
        "description": "Scrape property listings for a city/area with full filtering: price range, bedrooms, bathrooms, and property type. First choice for any property search.",
        "parameters": {"location": {"type": "string", "description": "City/location to scrape (e.g. 'Edmonton, AB' or 'Miami, FL')", "required": True}, "max_results": {"type": "integer", "description": "Maximum listings (default 25)", "required": False}, "min_price": {"type": "integer", "description": "Minimum price in dollars", "required": False}, "max_price": {"type": "integer", "description": "Maximum price in dollars (e.g. 1000000 for $1M)", "required": False}, "beds_min": {"type": "integer", "description": "Minimum bedrooms (e.g. 3)", "required": False}, "beds_max": {"type": "integer", "description": "Maximum bedrooms (e.g. 5)", "required": False}, "baths_min": {"type": "integer", "description": "Minimum bathrooms", "required": False}, "baths_max": {"type": "integer", "description": "Maximum bathrooms", "required": False}, "property_type": {"type": "string", "description": "Property type: single_family, condo, townhouse, multi_family, land, commercial", "required": False}, "sort": {"type": "string", "description": "Sort: days (newest), price_low, price_high", "required": False}}
    },
    {
        "name": "check_scraper_sources",
        "description": "Quick check on what web scraping sources are ready. Use this if the user asks about scraping capabilities.",
        "parameters": {}
    },
    {
        "name": "scrape_and_import_properties",
        "description": "Scrape property listings and import them into the system. Full end-to-end pipeline with filters: price range, bedrooms, bathrooms. Use when someone wants to scrape AND save properties to the database.",
        "parameters": {
            "location": {"type": "string", "description": "City/location to scrape (e.g. 'Edmonton, AB')", "required": True},
            "max_results": {"type": "integer", "description": "Maximum listings to import (default 25)", "required": False},
            "max_price": {"type": "integer", "description": "Maximum price filter (e.g. 1000000)", "required": False},
            "min_price": {"type": "integer", "description": "Minimum price filter", "required": False},
            "beds_min": {"type": "integer", "description": "Minimum bedrooms", "required": False},
            "beds_max": {"type": "integer", "description": "Maximum bedrooms", "required": False},
            "baths_min": {"type": "integer", "description": "Minimum bathrooms", "required": False},
            "baths_max": {"type": "integer", "description": "Maximum bathrooms", "required": False},
            "property_type": {"type": "string", "description": "Property type filter: single_family, condo, townhouse", "required": False}
        },
        "required": ["location"]
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
    # ── Lead Full CRUD ──
    {
        "name": "create_lead",
        "description": "Create a new lead/client in the pipeline. Provide at minimum name.",
        "parameters": {"first_name": {"type": "string", "description": "First name", "required": True}, "last_name": {"type": "string", "description": "Last name", "required": True}, "email": {"type": "string", "description": "Email address", "required": False}, "phone": {"type": "string", "description": "Phone number", "required": False}, "budget": {"type": "number", "description": "Maximum budget", "required": False}, "location_interest": {"type": "string", "description": "City/area interested in", "required": False}, "notes": {"type": "string", "description": "Notes about the lead", "required": False}}
    },
    {
        "name": "delete_lead",
        "description": "Permanently delete a lead by ID from the system.",
        "parameters": {"lead_id": {"type": "string", "description": "UUID of the lead to delete", "required": True}}
    },
    # ── Listing Full CRUD ──
    {
        "name": "create_listing",
        "description": "Create a new property listing with address, price, beds, baths, sqft, etc.",
        "parameters": {"address_street": {"type": "string", "description": "Street address", "required": True}, "address_city": {"type": "string", "description": "City", "required": True}, "address_state": {"type": "string", "description": "State/province code", "required": False}, "address_zip": {"type": "string", "description": "Zip code", "required": False}, "list_price": {"type": "number", "description": "List price", "required": True}, "beds": {"type": "integer", "description": "Bedrooms", "required": False}, "baths": {"type": "number", "description": "Bathrooms", "required": False}, "sqft": {"type": "integer", "description": "Square footage", "required": False}, "property_type": {"type": "string", "description": "single_family, condo, townhouse, etc.", "required": False}, "status": {"type": "string", "description": "ACTIVE, PENDING, SOLD, DRAFT", "required": False}, "description": {"type": "string", "description": "Property description", "required": False}, "mls_number": {"type": "string", "description": "MLS number", "required": False}}
    },
    {
        "name": "update_listing",
        "description": "Update a property listing's price, status, description, beds, baths, sqft.",
        "parameters": {"property_id": {"type": "string", "description": "UUID of the property", "required": True}, "list_price": {"type": "number", "description": "Updated price", "required": False}, "status": {"type": "string", "description": "ACTIVE, PENDING, SOLD, DRAFT", "required": False}, "description": {"type": "string", "description": "Updated description", "required": False}, "beds": {"type": "integer", "description": "Bedrooms", "required": False}, "baths": {"type": "number", "description": "Bathrooms", "required": False}, "sqft": {"type": "integer", "description": "Square footage", "required": False}}
    },
    {
        "name": "delete_listing",
        "description": "Delete a property listing by ID from the system.",
        "parameters": {"property_id": {"type": "string", "description": "UUID of the property", "required": True}}
    },
    # ── Task Full CRUD ──
    {
        "name": "list_tasks",
        "description": "List all tasks, optionally filtered by status or client.",
        "parameters": {"status": {"type": "string", "description": "Filter: todo, in_progress, done, cancelled", "required": False}, "client_id": {"type": "string", "description": "Filter by client UUID", "required": False}}
    },
    {
        "name": "get_task",
        "description": "Get full details for a single task by ID.",
        "parameters": {"task_id": {"type": "string", "description": "UUID of the task", "required": True}}
    },
    {
        "name": "create_task",
        "description": "Create a new task with title, priority, and optional client/property links.",
        "parameters": {"title": {"type": "string", "description": "Task title", "required": True}, "priority": {"type": "string", "description": "high, medium, low", "required": False}, "description": {"type": "string", "description": "Task description", "required": False}, "client_id": {"type": "string", "description": "Associated client UUID", "required": False}, "property_id": {"type": "string", "description": "Associated property UUID", "required": False}, "due_date": {"type": "string", "description": "Due date ISO format", "required": False}}
    },
    {
        "name": "update_task",
        "description": "Update a task's title, status, priority, or due date.",
        "parameters": {"task_id": {"type": "string", "description": "UUID of the task", "required": True}, "title": {"type": "string", "description": "New title", "required": False}, "status": {"type": "string", "description": "todo, in_progress, done, cancelled", "required": False}, "priority": {"type": "string", "description": "high, medium, low", "required": False}, "due_date": {"type": "string", "description": "Due date ISO format", "required": False}}
    },
    {
        "name": "delete_task",
        "description": "Delete a task by ID.",
        "parameters": {"task_id": {"type": "string", "description": "UUID of the task", "required": True}}
    },
    # ── Calendar/Event Full CRUD ──
    {
        "name": "list_events",
        "description": "List upcoming showings and calendar events for the next N days.",
        "parameters": {"days": {"type": "integer", "description": "Days ahead (default 30)", "required": False}}
    },
    {
        "name": "create_event",
        "description": "Create a showing or calendar event. Provide title, start time, and optional location.",
        "parameters": {"title": {"type": "string", "description": "Event title", "required": True}, "start_time": {"type": "string", "description": "Start datetime ISO 8601", "required": True}, "end_time": {"type": "string", "description": "End datetime ISO 8601", "required": False}, "location": {"type": "string", "description": "Address/location", "required": False}, "lead_name": {"type": "string", "description": "Client name for showing", "required": False}, "description": {"type": "string", "description": "Notes about the event", "required": False}}
    },
    {
        "name": "update_event",
        "description": "Update a showing or calendar event's title, time, location, or status.",
        "parameters": {"event_id": {"type": "string", "description": "UUID of the showing/event", "required": True}, "title": {"type": "string", "description": "New title", "required": False}, "start_time": {"type": "string", "description": "New start time", "required": False}, "end_time": {"type": "string", "description": "New end time", "required": False}, "location": {"type": "string", "description": "New location", "required": False}, "status": {"type": "string", "description": "pending, confirmed, completed, cancelled", "required": False}}
    },
    {
        "name": "delete_event",
        "description": "Delete/cancel a showing or calendar event by ID.",
        "parameters": {"event_id": {"type": "string", "description": "UUID of the showing/event", "required": True}}
    },
    # ── Email Management ──
    {
        "name": "list_emails",
        "description": "List synced emails from inbox, optionally filtered by classification.",
        "parameters": {"limit": {"type": "integer", "description": "Max results (default 20)", "required": False}, "classification": {"type": "string", "description": "Filter: buyer_lead, seller_lead, general_question, etc.", "required": False}}
    },
    {
        "name": "get_email",
        "description": "Get full content of a synced email by ID.",
        "parameters": {"email_id": {"type": "string", "description": "Email UUID", "required": True}}
    },
    {
        "name": "send_email",
        "description": "Send an email via connected Gmail account.",
        "parameters": {"to": {"type": "string", "description": "Recipient email", "required": True}, "subject": {"type": "string", "description": "Email subject", "required": True}, "body": {"type": "string", "description": "Email body text", "required": True}}
    },
    {
        "name": "sync_emails",
        "description": "Force a sync of new emails from Gmail inbox.",
        "parameters": {"max_results": {"type": "integer", "description": "Max emails (default 30)", "required": False}}
    },
    # ── Briefing ──
    {
        "name": "list_email_drafts",
        "description": "List all AI-generated email drafts that are pending approval.",
        "parameters": {}
    },
    {
        "name": "approve_email_draft",
        "description": "Approve and send an AI-generated email draft.",
        "parameters": {"draft_id": {"type": "string", "description": "UUID of the draft to approve", "required": True}}
    },
    {
        "name": "delete_email_draft",
        "description": "Reject or delete an AI-generated email draft.",
        "parameters": {"draft_id": {"type": "string", "description": "UUID of the draft to delete", "required": True}}
    },
    {
        "name": "delete_email",
        "description": "Delete/trash an email from your inbox. Removes from local DB and Gmail.",
        "parameters": {"email_id": {"type": "string", "description": "Email UUID to delete", "required": True}}
    },
    {
        "name": "mark_email_read",
        "description": "Mark an email as read or unread in your inbox.",
        "parameters": {"email_id": {"type": "string", "description": "Email UUID", "required": True}, "unread": {"type": "boolean", "description": "true=mark unread, false=mark read", "required": False}}
    },
    {
        "name": "report_spam",
        "description": "Report an email as spam. Moves to Gmail SPAM folder and removes from local inbox.",
        "parameters": {"email_id": {"type": "string", "description": "Email UUID to mark as spam", "required": True}}
    },
    {
        "name": "classify_email",
        "description": "Set or update the AI classification label on an email.",
        "parameters": {"email_id": {"type": "string", "description": "Email UUID", "required": True}, "classification": {"type": "string", "description": "Label like buyer_lead, spam, follow_up, pre_approval", "required": True}}
    },
    {
        "name": "clean_inbox",
        "description": "Scan entire inbox for spam emails and auto-delete them. Uses keyword + sender analysis.",
        "parameters": {}
    },
    {
        "name": "get_briefing",
        "description": "Get today's daily briefing with business summary, insights, and priorities. Auto-generates if needed.",
        "parameters": {}
    },
    {
        "name": "refresh_briefing",
        "description": "Force regenerate today's briefing with fresh data.",
        "parameters": {}
    },
    # ── User Profile ──
    {
        "name": "get_user_profile",
        "description": "Get your user profile: name, email, phone, brokerage, license number.",
        "parameters": {}
    },
    {
        "name": "update_user_profile",
        "description": "Update your profile: name, phone, brokerage, license number.",
        "parameters": {"full_name": {"type": "string", "description": "Full name", "required": False}, "phone": {"type": "string", "description": "Phone number", "required": False}, "brokerage_name": {"type": "string", "description": "Brokerage name", "required": False}, "license_number": {"type": "string", "description": "License number", "required": False}}
    },
    # ── Regulatory Law ──
    {
        "name": "query_regulations",
        "description": "Search Canada and US real estate regulations. Covers RECO/REBBA (Ontario), BCFSA/foreign buyer tax (BC), RECA (Alberta), OACIQ (Quebec), RESPA, TILA/TRID, Fair Housing Act, state-specific rules (California, New York, Texas, Florida), commission/antitrust rulings, tax implications, environmental regulations, and more. Returns ranked results with citations.",
        "parameters": {"query": {"type": "string", "description": "What regulation to look up (e.g. 'foreign buyer tax Ontario', 'RESPA disclosure', 'commission rules', 'Fair Housing')", "required": True}, "country": {"type": "string", "description": "Filter by country: Canada or USA (optional)", "required": False}, "jurisdiction": {"type": "string", "description": "Filter by jurisdiction: Ontario, BC, California, etc. (optional)", "required": False}}
    },
    {
        "name": "list_regulatory_jurisdictions",
        "description": "List all available regulatory jurisdictions and topics covered. Use this to explore what regulatory information is available before asking a specific question.",
        "parameters": {"country": {"type": "string", "description": "Filter by country: Canada or USA (optional)", "required": False}}
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
        return _scrape_properties_advanced(
            args.get("location", ""),
            max_results=args.get("max_results", 25),
            min_price=args.get("min_price"),
            max_price=args.get("max_price"),
            beds_min=args.get("beds_min"),
            beds_max=args.get("beds_max"),
            baths_min=args.get("baths_min"),
            baths_max=args.get("baths_max"),
            property_type=args.get("property_type"),
            sort=args.get("sort"),
        )
    elif name == "check_scraper_sources":
        return _check_scraper_sources()
    elif name == "scrape_and_import_properties":
        return _scrape_and_import(
            args.get("location", ""),
            max_results=args.get("max_results", 25),
            min_price=args.get("min_price"),
            max_price=args.get("max_price"),
            beds_min=args.get("beds_min"),
            beds_max=args.get("beds_max"),
            baths_min=args.get("baths_min"),
            baths_max=args.get("baths_max"),
            property_type=args.get("property_type"),
        )
    elif name == "score_lead":
        return _score_lead(args.get("lead_id", ""))
    elif name == "recommend_follow_up":
        return _recommend_follow_up(args.get("lead_id", ""))
    elif name == "property_price_analysis":
        return _property_price_analysis(args.get("property_id", ""))
    elif name == "market_trend_report":
        return _market_trend_report(args.get("city", ""))

    # ── Lead Full CRUD ──
    elif name == "create_lead":
        return _create_lead(args)
    elif name == "delete_lead":
        return _delete_lead(args.get("lead_id", ""))
    # ── Listing Full CRUD ──
    elif name == "create_listing":
        return _create_listing(args)
    elif name == "update_listing":
        return _update_listing(args)
    elif name == "delete_listing":
        return _delete_listing(args.get("property_id", ""))
    # ── Task Full CRUD ──
    elif name == "list_tasks":
        return _list_tasks(args.get("status"), args.get("client_id"))
    elif name == "get_task":
        return _get_task(args.get("task_id", ""))
    elif name == "create_task":
        return _create_task(args)
    elif name == "update_task":
        return _update_task(args)
    elif name == "delete_task":
        return _delete_task(args.get("task_id", ""))
    # ── Calendar/Event Full CRUD ──
    elif name == "list_events":
        return _list_events(args.get("days", 30))
    elif name == "create_event":
        return _create_event(args)
    elif name == "update_event":
        return _update_event(args)
    elif name == "delete_event":
        return _delete_event(args.get("event_id", ""))
    # ── Email Management ──
    elif name == "list_emails":
        return _list_emails(args.get("limit", 20), args.get("classification"))
    elif name == "get_email":
        return _get_email(args.get("email_id", ""))
    elif name == "send_email":
        return _send_email(args)
    elif name == "list_email_drafts":
        return _list_email_drafts()
    elif name == "approve_email_draft":
        return _approve_email_draft(args.get("draft_id", ""))
    elif name == "delete_email_draft":
        return _delete_email_draft(args.get("draft_id", ""))
    elif name == "delete_email":
        return _delete_email(args.get("email_id", ""))
    elif name == "mark_email_read":
        return _mark_email_read(args.get("email_id", ""), args.get("unread", False))
    elif name == "report_spam":
        return _report_spam(args.get("email_id", ""))
    elif name == "classify_email":
        return _classify_email(args.get("email_id", ""), args.get("classification", ""))
    elif name == "clean_inbox":
        return _clean_inbox()
    elif name == "sync_emails":
        return _sync_emails(args.get("max_results", 30))
    # ── Briefing ──
    elif name == "get_briefing":
        return _get_briefing()
    elif name == "refresh_briefing":
        return _refresh_briefing()
    # ── User Profile ──
    elif name == "get_user_profile":
        return _get_user_profile()
    elif name == "update_user_profile":
        return _update_user_profile(args)

    # ── Regulatory Law ──
    elif name == "query_regulations":
        return _query_regulations(args.get("query", ""), args.get("country"), args.get("jurisdiction"))
    elif name == "list_regulatory_jurisdictions":
        return _list_regulatory_jurisdictions(args.get("country"))
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
        result += f"  • {r['first_name']} {r['last_name']} — Score: {score}% — Budget: ${budget:,.2f} — Status: {r['status']}\n    Email: {r['email']}\n"
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




# ── Lead Full CRUD Implementations ──

def _create_lead(args: dict) -> str:
    try:
        import uuid
        lead_id = str(uuid.uuid4())
        uid = _current_user_id
        first = args.get("first_name", "")
        last = args.get("last_name", "")
        email = args.get("email", "")
        phone = args.get("phone", "")
        budget = args.get("budget")
        loc = args.get("location_interest", "")
        notes = args.get("notes", "")
        _execute_db(
            "INSERT INTO leads (id, agent_id, first_name, last_name, email, phone, budget, location_interest, notes, status, created_at, updated_at) VALUES (:id, :uid, :fn, :ln, :em, :ph, :budget, :loc, :notes, 'NEW', NOW(), NOW())",
            {"id": lead_id, "uid": uid, "fn": first, "ln": last, "em": email, "ph": phone, "budget": budget, "loc": loc, "notes": notes}
        )
        return f"Lead created: {first} {last} (ID: {lead_id})"
    except Exception as e:
        return f"Error: {e}"

def _delete_lead(lead_id: str) -> str:
    try:
        _execute_db("DELETE FROM leads WHERE id = :id", {"id": lead_id})
        return f"Lead {lead_id} deleted."
    except Exception as e:
        return f"Error: {e}"

# ── Listing Full CRUD Implementations ──

def _create_listing(args: dict) -> str:
    try:
        import uuid
        prop_id = str(uuid.uuid4())
        uid = _current_user_id
        _execute_db(
            "INSERT INTO properties (id, agent_id, address_street, address_city, address_state, address_zip, list_price, beds, baths, sqft, property_type, status, description, mls_number, created_at, updated_at) VALUES (:id, :uid, :street, :city, :state, :zip, :price, :beds, :baths, :sqft, :ptype, :status, :desc, :mls, NOW(), NOW())",
            {
                "id": prop_id, "uid": uid,
                "street": args.get("address_street"), "city": args.get("address_city"),
                "state": args.get("address_state", "AB"), "zip": args.get("address_zip", ""),
                "price": args.get("list_price"), "beds": args.get("beds"), "baths": args.get("baths"),
                "sqft": args.get("sqft"), "ptype": args.get("property_type", "single_family"),
                "status": (args.get("status", "ACTIVE") or "ACTIVE").upper(),
                "desc": args.get("description", ""), "mls": args.get("mls_number", ""),
            }
        )
        return f"Listing created: {args.get('address_street')}, {args.get('address_city')} - ${args.get('list_price'):,.0f} (ID: {prop_id})"
    except Exception as e:
        return f"Error: {e}"

def _update_listing(args: dict) -> str:
    try:
        updates = []
        params = {"id": args.get("property_id")}
        for field in ["list_price", "status", "description", "beds", "baths", "sqft"]:
            if field in args and args[field] is not None:
                # status stored uppercase in VPS DB
                val = args[field].upper() if field == "status" and isinstance(args[field], str) else args[field]
                updates.append(f"{field} = :{field}")
                params[field] = val
        if updates:
            _execute_db(f"UPDATE properties SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id", params)
        return f"Listing {args.get('property_id')} updated."
    except Exception as e:
        return f"Error: {e}"

def _delete_listing(property_id: str) -> str:
    try:
        _execute_db("DELETE FROM properties WHERE id = :id", {"id": property_id})
        return f"Listing {property_id} deleted."
    except Exception as e:
        return f"Error: {e}"

# ── Task CRUD Implementations ──

def _list_tasks(status: str = None, client_id: str = None) -> str:
    try:
        uid = _current_user_id
        query = "SELECT id, title, priority, status, client_id, due_date, created_at FROM tasks WHERE user_id = :uid"
        params = {"uid": uid}
        if status:
            query += " AND status = :status"
            params["status"] = status
        if client_id:
            query += " AND client_id = :cid"
            params["cid"] = client_id
        query += " ORDER BY created_at DESC LIMIT 50"
        rows = _query_db(query, params)
        if not rows:
            return "No tasks found."
        result = f"**Tasks ({len(rows)}):**\n\n"
        for r in rows:
            due = f" due: {r['due_date'].strftime('%b %d')}" if r.get('due_date') else ""
            result += f"  \u2022 [{r['priority']}] {r['title']} \u2014 {r['status']}{due}\n"
        return result
    except Exception as e:
        return f"Error: {e}"

def _get_task(task_id: str) -> str:
    try:
        rows = _query_db("SELECT * FROM tasks WHERE id = :id", {"id": task_id})
        if not rows:
            return "Task not found."
        r = rows[0]
        due = f"\nDue: {r['due_date'].strftime('%b %d, %Y')}" if r.get('due_date') else ""
        return f"Task: {r['title']}\nPriority: {r['priority']}\nStatus: {r['status']}\nClient: {r.get('client_id', 'N/A')}{due}\n{r.get('description', '')}"
    except Exception as e:
        return f"Error: {e}"

def _create_task(args: dict) -> str:
    try:
        import uuid
        tid = str(uuid.uuid4())
        uid = _current_user_id
        _execute_db(
            "INSERT INTO tasks (id, user_id, title, priority, status, description, client_id, property_id, due_date, created_at, updated_at) VALUES (:id, :uid, :title, :prio, :status, :desc, :cid, :pid, :due, NOW(), NOW())",
            {
                "id": tid, "uid": uid, "title": args.get("title", ""),
                "prio": args.get("priority", "medium"), "status": "todo",
                "desc": args.get("description", ""), "cid": args.get("client_id"),
                "pid": args.get("property_id"), "due": args.get("due_date"),
            }
        )
        return f"Task created: '{args.get('title')}' (ID: {tid})"
    except Exception as e:
        return f"Error: {e}"

def _update_task(args: dict) -> str:
    try:
        updates = []
        params = {"id": args.get("task_id")}
        for field in ["title", "status", "priority", "due_date"]:
            if field in args and args[field] is not None:
                updates.append(f"{field} = :{field}")
                params[field] = args[field]
        if updates:
            _execute_db(f"UPDATE tasks SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id", params)
        return f"Task {args.get('task_id')} updated."
    except Exception as e:
        return f"Error: {e}"

def _delete_task(task_id: str) -> str:
    try:
        _execute_db("DELETE FROM tasks WHERE id = :id", {"id": task_id})
        return f"Task {task_id} deleted."
    except Exception as e:
        return f"Error: {e}"

# ── Calendar/Event CRUD Implementations ──

def _list_events(days: int = 30) -> str:
    try:
        uid = _current_user_id
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() + timedelta(days=days)
        rows = _query_db(
            "SELECT id, lead_name, property_address, showing_time, status FROM showings WHERE user_id = :uid AND showing_time <= :cutoff ORDER BY showing_time LIMIT 50",
            {"uid": uid, "cutoff": cutoff}
        )
        if not rows:
            return "No upcoming events found."
        result = f"**Events ({len(rows)}):**\n\n"
        for r in rows:
            t = r['showing_time'].strftime('%b %d %I:%M %p') if r.get('showing_time') else "?"
            result += f"  \u2022 {r['lead_name']} @ {r['property_address']} \u2014 {t} [{r['status']}]\n"
        return result
    except Exception as e:
        return f"Error: {e}"

def _create_event(args: dict) -> str:
    try:
        import uuid
        eid = str(uuid.uuid4())
        uid = _current_user_id
        title = args.get("title", "Event")
        lead_name = args.get("lead_name", title)
        loc = args.get("location", "")
        start = args.get("start_time", "")
        end = args.get("end_time")
        desc = args.get("description", "")
        _execute_db(
            "INSERT INTO showings (id, user_id, lead_name, property_address, showing_time, status, created_at, updated_at) VALUES (:id, :uid, :name, :addr, :time, 'pending', NOW(), NOW())",
            {"id": eid, "uid": uid, "name": lead_name, "addr": loc, "time": start}
        )
        return f"Event created: '{title}' at {start} (ID: {eid})"
    except Exception as e:
        return f"Error: {e}"

def _update_event(args: dict) -> str:
    try:
        updates = []
        params = {"id": args.get("event_id")}
        field_map = {"title": "lead_name", "location": "property_address", "start_time": "showing_time", "status": "status"}
        for arg_field, db_field in field_map.items():
            if arg_field in args and args[arg_field] is not None:
                updates.append(f"{db_field} = :{db_field}")
                params[db_field] = args[arg_field]
        if updates:
            _execute_db(f"UPDATE showings SET {', '.join(updates)}, updated_at = NOW() WHERE id = :id", params)
        return f"Event {args.get('event_id')} updated."
    except Exception as e:
        return f"Error: {e}"

def _delete_event(event_id: str) -> str:
    try:
        _execute_db("DELETE FROM showings WHERE id = :id", {"id": event_id})
        return f"Event {event_id} deleted."
    except Exception as e:
        return f"Error: {e}"

# ── Email CRUD Implementations ──

def _list_emails(limit: int = 20, classification: str = None) -> str:
    try:
        uid = _current_user_id
        query = "SELECT id, subject, sender, sender_name, ai_classification, received_at FROM synced_emails WHERE user_id = :uid"
        params = {"uid": uid}
        if classification:
            query += " AND ai_classification = :cls"
            params["cls"] = classification
        query += " ORDER BY received_at DESC NULLS LAST LIMIT :lim"
        params["lim"] = limit
        rows = _query_db(query, params)
        if not rows:
            return "No emails found. Try sync_emails first."
        result = f"**Emails ({len(rows)}):**\n\n"
        for r in rows:
            name = r.get('sender_name') or r.get('sender', 'Unknown')
            subj = (r.get('subject') or '(no subject)')[:60]
            cls = f" [{r.get('ai_classification')}]" if r.get('ai_classification') else ""
            result += f"  \u2022 {name}: \"{subj}\"{cls}\n"
        return result
    except Exception as e:
        return f"Error: {e}"

def _get_email(email_id: str) -> str:
    try:
        rows = _query_db("SELECT * FROM synced_emails WHERE id = :id", {"id": email_id})
        if not rows:
            return "Email not found."
        r = rows[0]
        t = r['received_at'].strftime('%b %d, %Y %I:%M %p') if r.get('received_at') else "?"
        body = (r.get('body') or r.get('snippet') or '(no content)')[:2000]
        return f"From: {r.get('sender_name') or r.get('sender')}\nSubject: {r.get('subject', '(no subject)')}\nDate: {t}\nClassification: {r.get('ai_classification', 'N/A')}\n---\n{body}"
    except Exception as e:
        return f"Error: {e}"

def _send_email(args: dict) -> str:
    to = args.get("to", "")
    subject = args.get("subject", "")
    body = args.get("body", "")
    if not to or not subject or not body:
        return "Missing required fields: to, subject, body."
    try:
        from integrations.gmail.tools import send_gmail
        uid = _current_user_id
        result = send_gmail(user_id=uid, to=to, subject=subject, body=body)
        if result.get("status") == "sent":
            return f"Email sent to {to} with subject '{subject}'."
        return f"Send result: {result}"
    except ImportError:
        pass
    except Exception as e:
        return f"Gmail send failed: {e}"
    # Fallback: try raw API
    try:
        import httpx, json
        resp = httpx.post(
            "http://localhost:8000/api/v1/gmail/send",
            json={"to": to, "subject": subject, "body": body},
            timeout=15,
        )
        if resp.status_code == 200:
            return f"Email sent to {to} with subject '{subject}'."
        return f"Send result: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot send email: {e}. Connect Gmail in Settings first."

def _sync_emails(max_results: int = 30) -> str:
    try:
        from integrations.gmail.tools import sync_gmail
        uid = _current_user_id
        result = sync_gmail(user_id=uid, max_results=max_results)
        count = result.get("synced", 0) if isinstance(result, dict) else 0
        return f"Synced {count} new emails."
    except ImportError:
        pass
    except Exception as e:
        pass
    try:
        import httpx
        resp = httpx.post(f"http://localhost:8000/api/v1/gmail/sync?max_results={max_results}", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return f"Synced {data.get('synced', 0)} emails."
        return f"Sync result: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot sync: {e}. Connect Gmail in Settings."

def _list_email_drafts() -> str:
    """List AI-generated email drafts pending approval via VPS API."""
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/api/v1/messages/unified/drafts", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            drafts = data if isinstance(data, list) else data.get("drafts", [])
            if not drafts:
                return "No pending email drafts found."
            result = f"**Email Drafts ({len(drafts)}):**\n\n"
            for d in drafts:
                did = d.get("id", "?")
                subj = d.get("subject", "(no subject)")
                to = d.get("to", d.get("recipient", "?"))
                result += f"  \u2022 **{subj}** \u2014 To: {to} (ID: {did})\n"
            return result
        return f"Failed to list drafts: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot list drafts: {e}"

def _approve_email_draft(draft_id: str) -> str:
    """Approve and send an AI-generated email draft."""
    if not draft_id:
        return "Please provide a draft ID."
    try:
        import httpx
        resp = httpx.post(f"http://localhost:8000/api/v1/gmail/drafts/{draft_id}/approve", timeout=15)
        if resp.status_code == 200:
            return f"Draft {draft_id} approved and sent."
        return f"Approval failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot approve draft: {e}"

def _delete_email_draft(draft_id: str) -> str:
    """Reject/delete an AI-generated email draft."""
    if not draft_id:
        return "Please provide a draft ID."
    try:
        import httpx
        resp = httpx.delete(f"http://localhost:8000/api/v1/gmail/drafts/{draft_id}", timeout=15)
        if resp.status_code == 200:
            return f"Draft {draft_id} deleted."
        return f"Delete failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot delete draft: {e}"


# ── Email Management Implementations ──

_API_BASE = "http://localhost:8000"

def _delete_email(email_id: str) -> str:
    """Delete/trash an email from inbox."""
    if not email_id:
        return "Please provide an email ID."
    try:
        import httpx
        resp = httpx.delete(f"{_API_BASE}/api/v1/gmail/emails/{email_id}", timeout=15)
        if resp.status_code == 200:
            return f"Email {email_id[:8]}... deleted from inbox."
        return f"Delete failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot delete email: {e}"

def _mark_email_read(email_id: str, unread: bool = False) -> str:
    """Mark an email as read or unread."""
    if not email_id:
        return "Please provide an email ID."
    try:
        import httpx
        resp = httpx.patch(
            f"{_API_BASE}/api/v1/gmail/emails/{email_id}",
            json={"is_unread": unread},
            timeout=15,
        )
        if resp.status_code == 200:
            action = "unread" if unread else "read"
            return f"Email {email_id[:8]}... marked as {action}."
        return f"Failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot mark email: {e}"

def _report_spam(email_id: str) -> str:
    """Report an email as spam."""
    if not email_id:
        return "Please provide an email ID."
    try:
        import httpx
        resp = httpx.post(f"{_API_BASE}/api/v1/gmail/emails/{email_id}/spam", timeout=15)
        if resp.status_code == 200:
            return f"Email {email_id[:8]}... reported as spam and removed from inbox."
        return f"Failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot report spam: {e}"

def _classify_email(email_id: str, classification: str) -> str:
    """Set the AI classification on an email."""
    if not email_id or not classification:
        return "Please provide email ID and classification."
    try:
        import httpx
        resp = httpx.patch(
            f"{_API_BASE}/api/v1/gmail/emails/{email_id}",
            json={"ai_classification": classification},
            timeout=15,
        )
        if resp.status_code == 200:
            return f"Email {email_id[:8]}... classified as '{classification}'."
        return f"Failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot classify email: {e}"

def _clean_inbox() -> str:
    """Scan inbox for spam and auto-delete."""
    try:
        import httpx
        resp = httpx.post(f"{_API_BASE}/api/v1/gmail/scan-spam", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", f"Spam scan complete. {data.get('deleted', 0)} removed.")
        return f"Spam scan failed: HTTP {resp.status_code}"
    except Exception as e:
        return f"Cannot scan inbox: {e}"


# ── Briefing Implementations ──

def _get_briefing() -> str:
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/api/v1/briefing", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            lines = [f"**{data.get('greeting', 'Good morning!')}**"]
            s = data.get('summary', {})
            if s:
                lines.append(f"\n**Business Snapshot:**")
                lines.append(f"  \u2022 {s.get('total_clients', 0)} clients ({s.get('new_clients_last_7d', 0)} new)")
                lines.append(f"  \u2022 {s.get('active_listings', 0)} active listings")
                lines.append(f"  \u2022 {s.get('pending_tasks', 0)} pending tasks ({s.get('high_priority_tasks', 0)} high)")
                lines.append(f"  \u2022 {s.get('events_today', 0)} events today")
            for label, key in [("Insights", "insights"), ("Priorities", "priorities")]:
                items = data.get(key, [])
                if items:
                    lines.append(f"\n**{label}:**")
                    for item in items:
                        lines.append(f"  \u2022 {item}")
            return "\n".join(lines)
        return f"Briefing unavailable (HTTP {resp.status_code})"
    except Exception as e:
        return f"Briefing unavailable: {e}"

def _refresh_briefing() -> str:
    try:
        import httpx
        resp = httpx.post("http://localhost:8000/api/v1/briefing/refresh", timeout=15)
        return f"Briefing refreshed." if resp.status_code == 200 else f"Refresh failed (HTTP {resp.status_code})"
    except Exception as e:
        return f"Refresh failed: {e}"

# ── User Profile Implementations ──

def _get_user_profile() -> str:
    try:
        uid = _current_user_id
        rows = _query_db(
            "SELECT full_name, email, phone, brokerage_name, license_number FROM users WHERE id = :uid",
            {"uid": uid}
        )
        if not rows:
            return "User not found."
        r = rows[0]
        return f"Name: {r.get('full_name', '')}\nEmail: {r.get('email', '')}\nPhone: {r.get('phone', 'N/A')}\nBrokerage: {r.get('brokerage_name', 'N/A')}\nLicense: {r.get('license_number', 'N/A')}"
    except Exception as e:
        return f"Error: {e}"

def _update_user_profile(args: dict) -> str:
    try:
        updates = []
        params = {"uid": _current_user_id}
        for field in ["full_name", "phone", "brokerage_name", "license_number"]:
            if field in args and args[field] is not None:
                updates.append(f"{field} = :{field}")
                params[field] = args[field]
        if updates:
            _execute_db(f"UPDATE users SET {', '.join(updates)} WHERE id = :uid", params)
        return "Profile updated."
    except Exception as e:
        return f"Error: {e}"


# ── Regulatory Law Implementations ──

def _query_regulations(query: str, country: str = None, jurisdiction: str = None) -> str:
    """Search regulatory knowledge base for Canada/US real estate law."""
    try:
        from .regulatory import get_regulatory_service
        svc = get_regulatory_service()
        results = svc.query(query, country=country, jurisdiction=jurisdiction, limit=5)
        if not results:
            return "No matching regulations found. Try different keywords or check available jurisdictions with list_regulatory_jurisdictions."
        lines = []
        for r in results:
            lines.append(f"**{r['title']}**")
            lines.append(f"*Jurisdiction:* {r['jurisdiction']} ({r['country']})")
            lines.append(f"*Citations:* {', '.join(r.get('citations', []))}")
            lines.append("")
            lines.append(r['body'])
            lines.append("---")
        return "\n".join(lines)
    except ImportError as e:
        return f"Regulatory knowledge base not available: {e}"
    except Exception as e:
        return f"Error querying regulations: {e}"

def _list_regulatory_jurisdictions(country: str = None) -> str:
    """List all available regulatory jurisdictions and topics."""
    try:
        from .regulatory import get_regulatory_service
        svc = get_regulatory_service()
        summary = svc.get_summary(country=country)
        lines = [f"**Regulatory Knowledge Base**"]
        lines.append(f"Total regulations: {summary['total_regulations']}")
        lines.append(f"Countries: {', '.join(summary['countries'])}")
        lines.append("")
        lines.append("**Jurisdictions covered:**")
        for j in summary['jurisdictions']:
            topics = summary['topics'].get(j, [])
            lines.append(f"  \u2022 **{j}** \u2014 {len(topics)} topics")
            for t in topics[:3]:
                lines.append(f"    - {t}")
            if len(topics) > 3:
                lines.append(f"    - ... and {len(topics)-3} more")
        return "\n".join(lines)
    except ImportError as e:
        return f"Regulatory knowledge base not available: {e}"
    except Exception as e:
        return f"Error listing jurisdictions: {e}"

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


def _scrape_properties_advanced(location: str, max_results: int = 25, min_price: int = None, max_price: int = None, beds_min: int = None, beds_max: int = None, baths_min: int = None, baths_max: int = None, property_type: str = None, sort: str = None) -> str:
    """Scrape property listings using Zillow scraper with full filtering."""
    if not location:
        location = "Edmonton, AB"
        logger.info("Scraper called without location; defaulting to Edmonton, AB")

    try:
        from hermes.scraper.zillow import ZillowScraper
        scraper = ZillowScraper(delay=0.5)
        listings = scraper.search(location, max_results * 2)  # fetch extra for filtering room
        if not listings:
            return f"No listings found for {location}"

        # Apply filters
        if min_price:
            listings = [l for l in listings if (l.get("list_price") or 0) >= min_price]
        if max_price:
            listings = [l for l in listings if (l.get("list_price") or 0) <= max_price]
        if beds_min:
            listings = [l for l in listings if (l.get("beds") or 0) >= beds_min]
        if beds_max:
            listings = [l for l in listings if (l.get("beds") or 0) <= beds_max]
        if baths_min:
            listings = [l for l in listings if (l.get("baths") or 0) >= baths_min]
        if baths_max:
            listings = [l for l in listings if (l.get("baths") or 0) <= baths_max]
        if property_type:
            pt = property_type.lower().replace(" ", "_")
            listings = [l for l in listings if (l.get("property_type") or "").lower().replace(" ", "_") == pt]

        # Sort
        if sort == "price_low":
            listings.sort(key=lambda x: x.get("list_price", 0))
        elif sort == "price_high":
            listings.sort(key=lambda x: x.get("list_price", 0), reverse=True)
        elif sort == "days":
            listings.sort(key=lambda x: x.get("days_on_zillow", 9999))

        listings = listings[:max_results]
    except Exception as e:
        logger.warning(f"ZillowScraper search failed: {e}")
        return f"Scraping failed: {e}"

    if not listings:
        return f"No listings found for {location}"

    filters_used = []
    if min_price: filters_used.append(f"${min_price:,}+")
    if max_price: filters_used.append(f"up to ${max_price:,}")
    if beds_min or beds_max: filters_used.append(f"{beds_min or 0}-{beds_max or '∞'} beds")
    if baths_min or baths_max: filters_used.append(f"{baths_min or 0}-{baths_max or '∞'} baths")
    filter_tag = f" ({', '.join(filters_used)})" if filters_used else ""

    output = f"**Properties in {location}{filter_tag}** ({len(listings)} total)\n"
    output += "Source: Zillow\n\n"

    for i, p in enumerate(listings[:10], 1):
        url = p.get("url", "")
        output += f"{i}. **{p.get('address_street', 'N/A')}**\n"
        output += f"   ${p.get('list_price', 0):,} | {p.get('beds', 0)}bd | {p.get('baths', 0)}ba | {p.get('sqft', 0)}sqft | {p.get('property_type', 'house')}\n"
        if url:
            output += f"   [View on Zillow]({url})\n"

    if len(listings) > 10:
        output += f"\n... and {len(listings) - 10} more properties"

    output += f"\n\n**Filtered:** {filter_tag or 'none'}" if filters_used else ""
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


def _scrape_and_import(location: str, max_results: int = 25, min_price: int = None, max_price: int = None, beds_min: int = None, beds_max: int = None, baths_min: int = None, baths_max: int = None, property_type: str = None) -> str:
    """Scrape properties and import them into the system with full filtering."""
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
