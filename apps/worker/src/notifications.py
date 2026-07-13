"""
Notification system for Athena worker — email and SMS delivery.
Supports multiple providers: Gmail, SendGrid, Resend, Twilio.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# --- Provider Interface ---

class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> dict:
        pass

    @abstractmethod
    def provider_name(self) -> str:
        pass


# --- Email Providers ---

class GmailProvider(NotificationProvider):
    def __init__(self):
        from packages.integrations.gmail.client import GmailClient
        self.client = GmailClient()

    async def send(self, to: str, subject: str, body: str) -> dict:
        logger.info("Sending email via Gmail to %s", to)
        result = self.client.send_email(to, subject, body)
        return {"provider": "gmail", **result}

    def provider_name(self) -> str:
        return "gmail"


class SendGridProvider(NotificationProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send(self, to: str, subject: str, body: str) -> dict:
        logger.info("Sending email via SendGrid to %s", to)
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            client = SendGridAPIClient(self.api_key)
            message = Mail(
                from_email="athena@realty-ai.com",
                to_emails=to,
                subject=subject,
                html_content=body,
            )
            response = client.send(message)
            return {"provider": "sendgrid", "status": "sent", "status_code": response.status_code}
        except ImportError:
            return {"provider": "sendgrid", "status": "error", "error": "sendgrid not installed"}
        except Exception as e:
            logger.error("SendGrid send failed: %s", e)
            return {"provider": "sendgrid", "status": "error", "error": str(e)}

    def provider_name(self) -> str:
        return "sendgrid"


class ResendProvider(NotificationProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send(self, to: str, subject: str, body: str) -> dict:
        logger.info("Sending email via Resend to %s", to)
        try:
            import resend
            resend.api_key = self.api_key
            params = {
                "from": "Athena <athena@realty-ai.com>",
                "to": [to],
                "subject": subject,
                "html": body,
            }
            result = resend.Emails.send(params)
            return {"provider": "resend", "status": "sent", "id": result.get("id")}
        except ImportError:
            return {"provider": "resend", "status": "error", "error": "resend not installed"}
        except Exception as e:
            logger.error("Resend send failed: %s", e)
            return {"provider": "resend", "status": "error", "error": str(e)}

    def provider_name(self) -> str:
        return "resend"


# --- SMS Providers ---

class TwilioProvider(NotificationProvider):
    def __init__(self, account_sid: str, auth_token: str):
        from packages.integrations.sms.twilio import TwilioSMSClient
        self.client = TwilioSMSClient(account_sid, auth_token)

    async def send(self, to: str, subject: str, body: str) -> dict:
        logger.info("Sending SMS via Twilio to %s", to)
        result = self.client.send_sms(to, body)
        return {"provider": "twilio", **result}

    def provider_name(self) -> str:
        return "twilio"


# --- Notification Manager ---

@dataclass
class NotificationConfig:
    email_provider: str = "gmail"  # gmail, sendgrid, resend
    email_to: Optional[str] = None
    sms_provider: str = "twilio"  # twilio
    sms_to: Optional[str] = None


class NotificationManager:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self._email_provider: Optional[NotificationProvider] = None
        self._sms_provider: Optional[NotificationProvider] = None

    def _get_email_provider(self) -> NotificationProvider:
        if self._email_provider:
            return self._email_provider

        provider = self.config.email_provider.lower()
        if provider == "sendgrid":
            self._email_provider = SendGridProvider(os.environ.get("SENDGRID_API_KEY", ""))
        elif provider == "resend":
            self._email_provider = ResendProvider(os.environ.get("RESEND_API_KEY", ""))
        else:
            self._email_provider = GmailProvider()
        return self._email_provider

    def _get_sms_provider(self) -> NotificationProvider:
        if self._sms_provider:
            return self._sms_provider

        self._sms_provider = TwilioProvider(
            os.environ.get("TWILIO_ACCOUNT_SID", ""),
            os.environ.get("TWILIO_AUTH_TOKEN", ""),
        )
        return self._sms_provider

    async def send_briefing(self, briefing: str, subject: str = "Your Daily Athena Briefing") -> dict:
        results = {}

        if self.config.email_to:
            provider = self._get_email_provider()
            results["email"] = await provider.send(self.config.email_to, subject, briefing)

        if self.config.sms_to:
            # SMS gets truncated version
            sms_body = briefing[:1400] + "..." if len(briefing) > 1400 else briefing
            provider = self._get_sms_provider()
            results["sms"] = await provider.send(self.config.sms_to, subject, sms_body)

        return results


def create_notification_manager() -> NotificationManager:
    """Create notification manager from environment."""
    return NotificationManager(NotificationConfig(
        email_provider=os.environ.get("NOTIFICATION_EMAIL_PROVIDER", "gmail"),
        email_to=os.environ.get("NOTIFICATION_EMAIL_TO"),
        sms_provider=os.environ.get("NOTIFICATION_SMS_PROVIDER", "twilio"),
        sms_to=os.environ.get("NOTIFICATION_SMS_TO"),
    ))