"""
RealtyAI — Lead Agent Tools.

Responsibilities:
  - Qualify inbound leads
  - Score leads based on readiness
  - Summarize lead pipeline
  - Recommend next actions
"""
from langchain_core.tools import tool

from tools import get_hot_leads, search_leads, get_lead_count


@tool
def qualify_lead(name: str) -> dict:
    """Qualify a lead by full name. Returns AI score, reasoning, and recommended action.
    
    Args:
        name: Lead's full name, e.g. 'John Smith'.
    """
    parts = name.split(" ", 1)
    fname = parts[0]
    lname = parts[1] if len(parts) > 1 else ""
    leads = search_leads.invoke({"name": fname})
    lead = None
    for l in leads:
        if lname.lower() in l.get("last_name", "").lower():
            lead = l
            break
    if not lead and leads:
        lead = leads[0]
    if not lead:
        return {"error": f"Lead '{name}' not found in CRM"}

    score = lead.get("ai_score", 50)
    reason = lead.get("ai_score_reason", "No data available")

    if score >= 80:
        action = "📞 Call within 24 hours — high-intent buyer"
    elif score >= 60:
        action = "📧 Send listing alert — nurture with content"
    elif score >= 40:
        action = "📨 Add to drip campaign — needs warming"
    else:
        action = "⏸️ Low priority — check back in 30 days"

    return {
        "name": f"{lead['first_name']} {lead['last_name']}",
        "score": score,
        "reasoning": reason,
        "status": lead.get("status", "unknown"),
        "budget": f"${lead.get('budget', 0):,}" if lead.get("budget") else "Unknown",
        "timeline": lead.get("timeline", "unknown"),
        "recommended_action": action,
    }


@tool
def pipeline_summary() -> str:
    """Return a plain-language summary of the entire lead pipeline and top priorities."""
    counts = get_lead_count.invoke({})
    hot = get_hot_leads.invoke({})

    lines = [f"📊 **Pipeline Summary** — {counts['total']} total leads\n"]
    for status, count in sorted(counts["by_status"].items()):
        label = status.replace("_", " ").title()
        lines.append(f"  • {label}: {count}")
    lines.append("")

    if hot:
        lines.append("🔥 **Top Priorities:**")
        for l in hot[:5]:
            lines.append(f"  • {l['name']} (score: {l['score']}) — {l.get('timeline', '')}")
    else:
        lines.append("No leads in pipeline.")

    return "\n".join(lines)


@tool
def recommend_action(lead_name: str) -> str:
    """Recommend the single best next action for a specific lead.
    
    Args:
        lead_name: Full name of the lead to analyze.
    """
    result = qualify_lead.invoke({"name": lead_name})
    if "error" in result:
        return result["error"]
    return (
        f"**Recommended action for {result['name']}**\n\n"
        f"Score: {result['score']}/100\n"
        f"Status: {result['status']}\n"
        f"Timeline: {result['timeline']}\n\n"
        f"→ {result['recommended_action']}"
    )


LEAD_AGENT_TOOLS = [qualify_lead, pipeline_summary, recommend_action]
