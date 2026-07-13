from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


MOCK_CONTACTS: dict[str, dict[str, Any]] = {}


class CRMClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.example.com/crm") -> None:
        self.api_key = api_key
        self.base_url = base_url
        self._contacts: dict[str, dict[str, Any]] = dict(MOCK_CONTACTS)

    def create_contact(
        self, name: str, email: str, phone: str, notes: str = ""
    ) -> dict[str, Any]:
        """Create a new contact in the CRM."""
        logger.info("Creating contact: %s <%s>", name, email)
        contact_id = f"contact_{len(self._contacts) + 1:03d}"
        contact = {
            "id": contact_id,
            "name": name,
            "email": email,
            "phone": phone,
            "notes": notes,
            "lead_status": "new",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        self._contacts[contact_id] = contact
        return {"status": "created", **contact}

    def update_lead_status(
        self, lead_id: str, status: str
    ) -> dict[str, Any]:
        """Update the lead status for an existing contact."""
        logger.info("Updating lead %s to status: %s", lead_id, status)
        contact = self._contacts.get(lead_id)
        if contact is None:
            return {
                "status": "error",
                "error": f"Contact {lead_id} not found",
            }
        contact["lead_status"] = status
        contact["updated_at"] = datetime.utcnow().isoformat() + "Z"
        return {"status": "updated", **contact}
