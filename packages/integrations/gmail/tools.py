from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from langchain_core.tools import tool
except ImportError:

    def tool(func):
        return func


MOCK_LEADS = [
    {
        "id": "lead_001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "+1-555-0101",
        "message": "Looking to buy a 3BR home in Oakwood area.",
        "received_at": "2025-01-15T10:30:00Z",
    },
    {
        "id": "lead_002",
        "name": "Bob Martinez",
        "email": "bob@example.com",
        "phone": "+1-555-0102",
        "message": "Interested in selling my condo downtown.",
        "received_at": "2025-01-14T14:15:00Z",
    },
    {
        "id": "lead_003",
        "name": "Carol Chen",
        "email": "carol@example.com",
        "phone": "+1-555-0103",
        "message": "Need help with rental property management.",
        "received_at": "2025-01-13T09:00:00Z",
    },
]


MOCK_THREADS = {
    "thread_001": {
        "id": "thread_001",
        "subject": "New property inquiry - 123 Main St",
        "participants": ["buyer@example.com", "agent@realtyai.com"],
        "messages": [
            {
                "from": "buyer@example.com",
                "body": "I am interested in the property at 123 Main St. Is it still available?",
                "timestamp": "2025-01-15T10:30:00Z",
            },
            {
                "from": "agent@realtyai.com",
                "body": "Yes, it is still available! Would you like to schedule a viewing?",
                "timestamp": "2025-01-15T11:00:00Z",
            },
        ],
    }
}


@tool
def find_new_leads() -> list[dict[str, Any]]:
    """Search the agent's inbox for new lead-related emails and return structured lead data."""
    logger.info("Searching for new leads...")
    return MOCK_LEADS


@tool
def send_followup_email(
    to: str, subject: str, body: str
) -> dict[str, Any]:
    """Send a follow-up email to a prospective lead."""
    logger.info("Sending follow-up email to %s: %s", to, subject)
    return {
        "status": "mock_sent",
        "to": to,
        "subject": subject,
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }


@tool
def summarize_email_thread(
    thread_id: str,
) -> dict[str, Any]:
    """Summarize the contents of a given email thread by its thread ID."""
    logger.info("Summarizing thread %s", thread_id)
    thread = MOCK_THREADS.get(thread_id)
    if thread is None:
        return {
            "error": f"Thread {thread_id} not found",
            "summary": "",
        }

    summary_parts = []
    for msg in thread["messages"]:
        summary_parts.append(f"{msg['from']} wrote: {msg['body']}")

    return {
        "thread_id": thread_id,
        "subject": thread["subject"],
        "participants": thread["participants"],
        "summary": " | ".join(summary_parts),
        "message_count": len(thread["messages"]),
    }
