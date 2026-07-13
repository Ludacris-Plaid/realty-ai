from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False


MOCK_EVENTS = [
    {
        "id": "evt_001",
        "summary": "Property viewing - 123 Main St",
        "start": {"dateTime": "2025-01-20T10:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-20T11:00:00Z", "timeZone": "UTC"},
        "description": "Walkthrough with client Alice Johnson.",
    },
    {
        "id": "evt_002",
        "summary": "Listing photos - Downtown Condo",
        "start": {"dateTime": "2025-01-21T09:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-21T12:00:00Z", "timeZone": "UTC"},
        "description": "Photography session for the new downtown listing.",
    },
    {
        "id": "evt_003",
        "summary": "Client meeting - Bob Martinez",
        "start": {"dateTime": "2025-01-22T14:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2025-01-22T15:00:00Z", "timeZone": "UTC"},
        "description": "Discuss selling strategy for downtown condo.",
    },
]


class GoogleCalendarClient:
    def __init__(self, credentials: Any = None) -> None:
        self.credentials = credentials
        self.service = None
        if HAS_CALENDAR and credentials is not None:
            try:
                self.service = build("calendar", "v3", credentials=credentials)
            except Exception as e:
                logger.warning("Failed to build Calendar service: %s", e)

    def list_events(self, max_results: int = 10) -> list[dict[str, Any]]:
        """List upcoming calendar events."""
        if self.service is None:
            return MOCK_EVENTS[:max_results]
        try:
            now = datetime.now(timezone.utc).isoformat()
            results = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return results.get("items", [])
        except HttpError as e:
            logger.error("Calendar API error: %s", e)
            return MOCK_EVENTS[:max_results]

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a new calendar event."""
        if self.service is None:
            return {
                "status": "mock_created",
                "summary": summary,
                "start": start_time,
                "end": end_time,
            }
        try:
            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"},
            }
            created = (
                self.service.events()
                .insert(calendarId="primary", body=event)
                .execute()
            )
            return {"status": "created", "id": created["id"]}
        except HttpError as e:
            logger.error("Failed to create event: %s", e)
            return {"status": "error", "error": str(e)}

    def check_availability(self, date: str) -> list[dict[str, Any]]:
        """Check calendar availability for a given date (ISO format)."""
        if self.service is None:
            return [
                evt
                for evt in MOCK_EVENTS
                if evt["start"]["dateTime"].startswith(date)
            ]
        try:
            from datetime import timedelta

            start = datetime.fromisoformat(date).isoformat() + "Z"
            end = (
                datetime.fromisoformat(date) + timedelta(days=1)
            ).isoformat() + "Z"
            results = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start,
                    timeMax=end,
                    singleEvents=True,
                )
                .execute()
            )
            return results.get("items", [])
        except HttpError as e:
            logger.error("Availability check error: %s", e)
            return []
