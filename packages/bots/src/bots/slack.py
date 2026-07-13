"""
Slack Bot Adapter for Athena.

Handles Slack Events API via webhook, routes messages
to the Athena agent, and sends responses back to the channel/dm.

Supports both env-var tokens (global/default) and runtime tokens
(from user-configurable settings in the database).
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve(env_key: str, override: str = "") -> str:
    """Return override value if provided, else fall back to env var."""
    return override or os.environ.get(env_key, "")


def is_configured(bot_token: str = "", signing_secret: str = "") -> bool:
    """Check if Slack bot is configured."""
    bt = _resolve("SLACK_BOT_TOKEN", bot_token)
    ss = _resolve("SLACK_SIGNING_SECRET", signing_secret)
    return bool(bt) and bool(ss)


def verify_slack_signature(headers: dict, body: str, signing_secret: str = "") -> bool:
    """Verify Slack signing secret to confirm request authenticity."""
    secret = _resolve("SLACK_SIGNING_SECRET", signing_secret)
    if not secret:
        return True  # Skip verification if not configured
    import hashlib
    import hmac
    timestamp = headers.get("x-slack-request-timestamp", "")
    signature = headers.get("x-slack-signature", "")
    if not timestamp or not signature:
        return False
    sig_basestring = f"v0:{timestamp}:{body}"
    expected = "v0=" + hmac.new(
        secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def send_message(channel: str, text: str, bot_token: str = "") -> dict:
    """Post a message to a Slack channel or DM."""
    bt = _resolve("SLACK_BOT_TOKEN", bot_token)
    if not bt:
        logger.warning("Cannot send Slack message: bot not configured")
        return {"ok": False}
    import httpx
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bt}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json={
            "channel": channel,
            "text": text,
            "mrkdwn": True,
        })
        return resp.json()


async def handle_event(event_data: dict, athena_handler, bot_token: str = "", signing_secret: str = "") -> dict:
    """Process an incoming Slack event (message or verification challenge)."""
    logger.info(f"Slack event received: {json.dumps(event_data)[:200]}")
    
    # Handle URL verification challenge
    if event_data.get("type") == "url_verification":
        return {"challenge": event_data.get("challenge", "")}
    
    # Handle Events API wrapper
    event = event_data.get("event", {})
    event_type = event.get("type")
    
    # Only handle message events from users (not bot's own messages)
    if event_type == "message" and not event.get("bot_id", False):
        text = event.get("text", "").strip()
        channel = event.get("channel")
        user = event.get("user")
        
        if not text or not channel:
            return {"ok": True}
        
        # Ignore thread replies for now
        if event.get("thread_ts"):
            return {"ok": True}
        
        # Route through Athena
        try:
            result = athena_handler(text)
            response = result.get("response", "I'm here. How can I help you?")
            await send_message(channel, response, bot_token)
        except Exception as e:
            logger.error(f"Slack Athena error: {e}")
            await send_message(channel, f"I encountered an error: {str(e)[:100]}", bot_token)
    
    return {"ok": True}
