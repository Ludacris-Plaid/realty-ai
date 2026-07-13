"""
RealtyAI — Model Gateway with Fallback Chain.

Primary: Featherless.ai API (open-source models < 15B)
Fallback: NVIDIA API (when Featherless is at capacity or rate-limited)

Both providers use OpenAI-compatible API format.
"""
import os
import logging
from typing import Optional
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
import httpx

logger = logging.getLogger(__name__)


# ─── Config (lazy-loaded from env) ────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

# Primary: Featherless
def get_featherless_base() -> str:
    return _env("LLM_API_BASE", "https://api.featherless.ai/v1")

def get_featherless_key() -> str:
    return _env("LLM_API_KEY", "")

# Fallback: NVIDIA
def get_nvidia_base() -> str:
    return _env("LLM_FALLBACK_API_BASE", "https://integrate.api.nvidia.com/v1")

def get_nvidia_key() -> str:
    return _env("LLM_FALLBACK_API_KEY", "")

def get_nvidia_model() -> str:
    return _env("LLM_FALLBACK_MODEL", "meta/llama-3.1-8b-instruct")

# Model names
def get_fast_model() -> str:
    return _env("LLM_DEFAULT_MODEL", "unsloth/Qwen2.5-7B-Instruct")

def get_premium_model() -> str:
    return _env("LLM_PREMIUM_MODEL", "unsloth/Qwen2.5-14B-Instruct")

def get_local_model() -> str:
    return _env("LLM_LOCAL_MODEL", "unsloth/gemma-2-9b-it")


# ─── Fallback State ────────────────────────────────────────────────────────────

_fallback_until: Optional[datetime] = None

def _should_use_fallback() -> bool:
    """Check if we're in fallback mode (after recent Featherless failure)."""
    global _fallback_until
    if _fallback_until is None:
        return False
    if datetime.utcnow() < _fallback_until:
        return True
    _fallback_until = None
    return False

def _enable_fallback(duration_seconds: int = 120):
    """Switch to fallback provider for a duration."""
    global _fallback_until
    _fallback_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
    logger.warning(f"Featherless failed, falling back to NVIDIA for {duration_seconds}s")


# ─── Model Factory with Fallback ───────────────────────────────────────────────

def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Get ChatOpenAI using primary (Featherless) or fallback (NVIDIA) provider.
    
    Auto-falls back to NVIDIA when Featherless returns capacity/rate-limit errors.
    Once in fallback, stays there for 2 minutes before retrying Featherless.
    
    Args:
        model_name: Model ID override. For fallback, uses NVIDIA's configured model.
    """
    if _should_use_fallback() or not get_featherless_key():
        # Use NVIDIA fallback — ignore model_name, force NVIDIA's model
        return ChatOpenAI(
            model=get_nvidia_model(),
            base_url=get_nvidia_base(),
            api_key=get_nvidia_key(),
            temperature=0.2,
        )

    # Use Featherless primary
    return ChatOpenAI(
        model=model_name or get_fast_model(),
        base_url=get_featherless_base(),
        api_key=get_featherless_key(),
        temperature=0.2,
    )


# ─── Direct Provider Access (for agent.py to handle fallback in LangGraph) ────

def get_primary_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Featherless only (no fallback)."""
    return ChatOpenAI(
        model=model_name or get_fast_model(),
        base_url=get_featherless_base(),
        api_key=get_featherless_key(),
        temperature=0.2,
    )

def get_fallback_model() -> ChatOpenAI:
    """NVIDIA only."""
    return ChatOpenAI(
        model=get_nvidia_model(),
        base_url=get_nvidia_base(),
        api_key=get_nvidia_key(),
        temperature=0.2,
    )


# ─── Health Checks ─────────────────────────────────────────────────────────────

def is_proxy_available() -> bool:
    """Check if primary API (Featherless) is reachable."""
    try:
        r = httpx.get(
            f"{get_featherless_base()}/models",
            headers={"Authorization": f"Bearer {get_featherless_key()}"},
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Fetch available models from Featherless."""
    try:
        r = httpx.get(
            f"{get_featherless_base()}/models",
            headers={"Authorization": f"Bearer {get_featherless_key()}"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return [m["id"] for m in data.get("data", [])]
        return []
    except Exception:
        return []
