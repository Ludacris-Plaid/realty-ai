"""
RealtyAI — Daily AI Briefing.

The "killer feature" — every morning, the agent receives:
  • Hot leads needing follow-up
  • Property listing performance
  • Upcoming schedule
  • Business insights
  • Marketing suggestions

Architecture:
    Briefing Agent
      ├── get_hot_leads() → top prospects
      ├── get_lead_count() → pipeline summary
      ├── get_active_listings() → property status
      └── (future) calendar tools → today's schedule
          
    Each section is compiled and returned as a structured briefing.
"""
from datetime import datetime
from typing import Optional

# Dual-context import: in the API, `briefing` is a top-level module (PYTHONPATH
# includes /packages/ai) so `tools` is top-level. In the worker it is imported as
# `packages.ai.briefing`, so `tools` is a relative sibling. Handle both.
try:
    from .tools import get_hot_leads, get_lead_count, get_active_listings
except ImportError:
    from tools import get_hot_leads, get_lead_count, get_active_listings


# ─── Briefing Sections ──────────────────────────────────────────────────────

def _greeting(agent_name: str = "Sarah") -> str:
    hour = datetime.utcnow().hour
    # Rough UTC-based greeting (could use timezone in production)
    if hour < 12:
        time_greet = "morning"
    elif hour < 17:
        time_greet = "afternoon"
    else:
        time_greet = "evening"
    return f"Good {time_greet}, {agent_name}."


def _lead_briefing() -> dict:
    """Compile a summary of top leads and pipeline status."""
    hot_leads = get_hot_leads.invoke({})
    counts = get_lead_count.invoke({})

    top_3 = hot_leads[:3]

    return {
        "hot_leads": top_3,
        "total": counts.get("total", 0),
        "by_status": counts.get("by_status", {}),
        "needs_follow_up": [l for l in hot_leads if l["score"] >= 80][:5],
    }


def _listing_briefing() -> dict:
    """Compile status of active listings."""
    listings = get_active_listings.invoke({})
    return {
        "total_active": len(listings),
        "listings": listings,
        "highest_price": max((l.get("list_price", 0) for l in listings), default=0),
    }


# ─── Briefing Compiler ──────────────────────────────────────────────────────

def generate_briefing(agent_name: str = "Sarah") -> str:
    """Generate a complete morning briefing for the agent.
    
    Returns a formatted string with all sections.
    """
    greeting = _greeting(agent_name)
    leads = _lead_briefing()
    listings = _listing_briefing()

    # Build briefing text
    sections = [
        f"# {greeting}",
        "",
        "Here is your daily briefing.",
        "",
    ]

    # Today's priorities
    sections.append("## Today's Priorities")
    sections.append("")
    if leads["needs_follow_up"]:
        sections.append("### 🔥 Hot Follow-ups")
        for lead in leads["needs_follow_up"]:
            sections.append(f"- **{lead['name']}** — Score: {lead['score']}/100 — {lead.get('timeline', '')}")
        sections.append("")
    else:
        sections.append("No urgent follow-ups today.")
        sections.append("")

    # Pipeline
    sections.append("### 📊 Lead Pipeline")
    sections.append(f"**Total:** {leads['total']} leads")
    for status, count in sorted(leads["by_status"].items()):
        sections.append(f"- {status}: {count}")
    sections.append("")

    # Listings
    if listings["listings"]:
        sections.append("### 🏠 Active Listings")
        sections.append(f"**Total active:** {listings['total_active']}")
        for prop in listings["listings"]:
            price = prop.get("list_price", 0)
            beds = prop.get("beds", "?")
            baths = prop.get("baths", "?")
            sections.append(f"- {prop.get('address_street', 'Unknown')} — ${price:,} — {beds}bd/{baths}ba")
        sections.append("")

    # Action items
    sections.append("## Suggested Actions")
    sections.append("")
    if leads["needs_follow_up"]:
        sections.append("1. Call or email your hot leads today")
    if listings["listings"]:
        sections.append(f"2. Review your {listings['total_active']} active listings")
        sections.append("3. Consider social media posts for your top listings")
    sections.append("4. Check your calendar for upcoming showings")
    sections.append("")

    # Closing
    sections.append("---")
    sections.append(f"*Briefing generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    sections.append("")
    sections.append("Need me to take action on any of these? Just ask!")

    return "\n".join(sections)


def get_briefing_data() -> dict:
    """Return structured briefing data (not formatted text)."""
    return {
        "greeting": _greeting(),
        "leads": _lead_briefing(),
        "listings": _listing_briefing(),
        "generated_at": datetime.utcnow().isoformat(),
    }
