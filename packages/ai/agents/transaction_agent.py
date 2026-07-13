"""
RealtyAI — Transaction Agent Tools.

Responsibilities:
  - Track contract deadlines
  - Identify conditions and contingencies
  - Generate reminders
  - Timeline management
"""
from datetime import datetime, timedelta
from langchain_core.tools import tool


@tool
def analyze_deadlines(closing_date: str, inspection_days: int = 7,
                      financing_days: int = 14) -> dict:
    """Analyze transaction deadlines from a closing date and generate a timeline.
    
    Args:
        closing_date: Expected closing date (YYYY-MM-DD).
        inspection_days: Days allowed for inspection period.
        financing_days: Days allowed for financing contingency.
    """
    try:
        close = datetime.strptime(closing_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    today = datetime.now()
    inspection_deadline = close - timedelta(days=inspection_days)
    financing_deadline = close - timedelta(days=financing_days)

    return {
        "closing_date": closing_date,
        "timeline": [
            {"milestone": "Inspection Deadline", "date": inspection_deadline.strftime("%Y-%m-%d"),
             "remaining_days": (inspection_deadline - today).days,
             "status": "⚠️ Due soon" if 0 <= (inspection_deadline - today).days <= 7 else "✅ On track" if (inspection_deadline - today).days > 7 else "🔴 Overdue"},
            {"milestone": "Financing Deadline", "date": financing_deadline.strftime("%Y-%m-%d"),
             "remaining_days": (financing_deadline - today).days,
             "status": "⚠️ Due soon" if 0 <= (financing_deadline - today).days <= 7 else "✅ On track" if (financing_deadline - today).days > 7 else "🔴 Overdue"},
            {"milestone": "Closing Day", "date": closing_date,
             "remaining_days": (close - today).days,
             "status": "⚠️ Due soon" if 0 <= (close - today).days <= 7 else "✅ On track" if (close - today).days > 7 else "🔴 Overdue"},
        ],
        "recommendations": [],
    }


@tool
def generate_reminder(transaction_type: str, detail: str, due_date: str) -> dict:
    """Generate a professional reminder for a transaction task.
    
    Args:
        transaction_type: Type (inspection, financing, closing, document).
        detail: What needs to happen.
        due_date: When it's due (YYYY-MM-DD).
    """
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    days_left = (due - datetime.now()).days
    urgency = "🔴 URGENT" if days_left <= 3 else "⚠️ Upcoming" if days_left <= 7 else "📅 On Horizon"

    return {
        "type": transaction_type,
        "detail": detail,
        "due_date": due_date,
        "days_remaining": days_left,
        "urgency": urgency,
        "reminder_text": f"{urgency}: {detail} — Due {due_date} ({days_left} days away)",
    }


TRANSACTION_AGENT_TOOLS = [analyze_deadlines, generate_reminder]
