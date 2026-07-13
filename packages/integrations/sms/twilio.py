from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client

    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False


MOCK_SENT = {
    "sid": "SM_mock_sid_001",
    "status": "mock_sent",
    "to": "",
    "body": "",
    "date_sent": "",
}


class TwilioSMSClient:
    def __init__(
        self, account_sid: str | None = None, auth_token: str | None = None
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.client = None
        if HAS_TWILIO and account_sid and auth_token:
            try:
                self.client = Client(account_sid, auth_token)
            except Exception as e:
                logger.warning("Failed to initialize Twilio client: %s", e)

    def send_sms(self, to: str, message: str) -> dict[str, Any]:
        """Send an SMS message to a given phone number."""
        logger.info("Sending SMS to %s", to)
        if self.client is None:
            result = dict(MOCK_SENT)
            result["to"] = to
            result["body"] = message
            result["date_sent"] = datetime.utcnow().isoformat() + "Z"
            return result
        try:
            sent = self.client.messages.create(
                body=message, from_=self._get_from_number(), to=to
            )
            return {
                "sid": sent.sid,
                "status": sent.status,
                "to": to,
                "body": message,
                "date_sent": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            logger.error("Failed to send SMS: %s", e)
            return {"status": "error", "error": str(e), "to": to}

    def _get_from_number(self) -> str:
        return "+15551234567"
