"""
Telegram Bot Adapter for Athena.

Handles incoming Telegram updates via webhook, routes messages
to the Athena agent, and sends responses back to the chat.

Supports both env-var tokens (global/default) and runtime tokens
(from user-configurable settings in the database).
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _resolve_token(override_token: str = "") -> str:
    """Return override token if provided, else fall back to env var."""
    return override_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")


def is_configured(token: str = "") -> bool:
    """Check if Telegram bot is configured with a token."""
    return bool(_resolve_token(token))


async def set_webhook(webhook_url: str, token: str = "") -> dict:
    """Register the webhook URL with Telegram API."""
    bot_token = _resolve_token(token)
    if not bot_token:
        return {"ok": False, "error": "Telegram bot not configured"}
    import httpx
    url = TELEGRAM_API_BASE.format(token=bot_token, method="setWebhook")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"url": webhook_url})
        return resp.json()


async def send_message(chat_id: int, text: str, token: str = "", parse_mode: str = "Markdown") -> dict:
    """Send a message to a Telegram chat."""
    bot_token = _resolve_token(token)
    if not bot_token:
        logger.warning("Cannot send Telegram message: bot not configured")
        return {"ok": False}
    import httpx
    url = TELEGRAM_API_BASE.format(token=bot_token, method="sendMessage")
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        result = resp.json()
        if not result.get("ok"):
            # Fallback: try with HTML parse mode
            payload["parse_mode"] = "HTML"
            resp2 = await client.post(url, json=payload)
            result2 = resp2.json()
            if not result2.get("ok"):
                # Last resort: plain text
                payload["parse_mode"] = ""
                resp3 = await client.post(url, json=payload)
                result3 = resp3.json()
                if not result3.get("ok"):
                    logger.warning(f"Telegram send failed: {result3}")
    return result


async def send_typing(chat_id: int, token: str = "") -> dict:
    """Show 'typing...' indicator in the chat."""
    bot_token = _resolve_token(token)
    if not bot_token:
        return {"ok": False}
    import httpx
    url = TELEGRAM_API_BASE.format(token=bot_token, method="sendChatAction")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"chat_id": chat_id, "action": "typing"})
        return resp.json()


async def handle_update(update_data: dict, athena_handler, token: str = "") -> dict:
    """Process an incoming Telegram update (message or callback)."""
    logger.info(f"Telegram update received: {json.dumps(update_data)[:200]}")
    
    message = update_data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    
    if not chat_id or not text:
        logger.warning(f"Ignored Telegram update: no chat_id or text")
        return {"ok": False, "error": "No chat_id or text"}
    
    # Show typing indicator
    await send_typing(chat_id, token)
    
    # Route through Athena
    try:
        result = athena_handler(text)
        response = result.get("response", "I'm here. How can I help you?")
        await send_message(chat_id, response, token)
        return {"ok": True, "chat_id": chat_id}
    except Exception as e:
        logger.error(f"Telegram Athena error: {e}")
        await send_message(chat_id, f"I encountered an error: {str(e)[:100]}", token)
        return {"ok": False, "error": str(e)}
