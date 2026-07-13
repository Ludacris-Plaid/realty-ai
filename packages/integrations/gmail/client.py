from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    HAS_GMAIL = True
except ImportError:
    HAS_GMAIL = False


MOCK_MESSAGES = [
    {
        "id": "msg_001",
        "threadId": "thread_001",
        "subject": "New property inquiry - 123 Main St",
        "from": "buyer@example.com",
        "snippet": "I am interested in the property at 123 Main St...",
        "labelIds": ["INBOX", "UNREAD"],
        "internalDate": "2025-01-15T10:30:00Z",
    },
    {
        "id": "msg_002",
        "threadId": "thread_002",
        "subject": "Listing update request for Downtown Condo",
        "from": "client@example.com",
        "snippet": "Could you send me more details about the downtown listing?",
        "labelIds": ["INBOX"],
        "internalDate": "2025-01-14T14:15:00Z",
    },
]


class GmailClient:
    def __init__(self, credentials: Any = None) -> None:
        self.credentials = credentials
        self.service = None
        if HAS_GMAIL and credentials is not None:
            try:
                self.service = build("gmail", "v1", credentials=credentials)
            except Exception as e:
                logger.warning("Failed to build Gmail service: %s", e)

    def get_messages(self, max_results: int = 20) -> list[dict[str, Any]]:
        """Retrieve messages from the user's inbox."""
        if self.service is None:
            return MOCK_MESSAGES[:max_results]
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", maxResults=max_results)
                .execute()
            )
            messages = results.get("messages", [])
            full_messages = []
            for msg in messages:
                details = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"])
                    .execute()
                )
                full_messages.append(details)
            return full_messages
        except HttpError as e:
            logger.error("Gmail API error: %s", e)
            return MOCK_MESSAGES[:max_results]

    def send_email(
        self, to: str, subject: str, body: str
    ) -> dict[str, Any]:
        """Send an email via Gmail."""
        if self.service is None:
            return {"status": "mock_sent", "to": to, "subject": subject}
        try:
            from email.mime.text import MIMEText
            import base64

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )
            return {"status": "sent", "id": sent["id"]}
        except HttpError as e:
            logger.error("Failed to send email: %s", e)
            return {"status": "error", "error": str(e)}

    def search_emails(self, query: str) -> list[dict[str, Any]]:
        """Search emails matching a query string."""
        if self.service is None:
            return [
                msg
                for msg in MOCK_MESSAGES
                if query.lower() in msg["subject"].lower()
                or query.lower() in msg["snippet"].lower()
            ]
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query)
                .execute()
            )
            messages = results.get("messages", [])
            full_messages = []
            for msg in messages:
                details = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"])
                    .execute()
                )
                full_messages.append(details)
            return full_messages
        except HttpError as e:
            logger.error("Gmail search error: %s", e)
            return []
