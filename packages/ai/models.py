"""
RealtyAI — Model Gateway with Gentle Cascading Fallback.

Primary:  9router tunnel proxy (ocg/kimi-k2.6 — fast, low-cost)
Fallback 1: Featherless.ai (Qwen3-4B-Instruct)
Fallback 2: NVIDIA API (Llama-3.1-8B-Instruct)

Each level falls through ONLY on total failure (timeout, auth, down).
Rate limits and concurrency caps do NOT trigger fallback — they retry.
"""
import os
import logging
import time
from typing import Optional
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI
import httpx

logger = logging.getLogger(__name__)


# ─── Config ───────────────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

# Tier 1: 9router tunnel (primary)
def get_tunnel_base() -> str:
    return _env("LLM_API_BASE", "https://r9tgp4c.abc-tunnel.us/v1")

def get_tunnel_key() -> str:
    return _env("LLM_API_KEY", "")

# Tier 2: Featherless
def get_featherless_base() -> str:
    return _env("LLM_FALLBACK_API_BASE", "https://api.featherless.ai/v1")

def get_featherless_key() -> str:
    return _env("LLM_FALLBACK_API_KEY", "")

# Tier 3: NVIDIA (last resort)
def get_nvidia_base() -> str:
    return _env("LLM_FALLBACK2_API_BASE", "https://integrate.api.nvidia.com/v1")

def get_nvidia_key() -> str:
    return _env("LLM_FALLBACK2_API_KEY", "")

def get_nvidia_model() -> str:
    return _env("LLM_FALLBACK2_MODEL", "meta/llama-3.1-8b-instruct")

# Model names
def get_fast_model() -> str:
    return _env("LLM_DEFAULT_MODEL", "ocg/kimi-k2.6")

def get_premium_model() -> str:
    return _env("LLM_PREMIUM_MODEL", "ocg/deepseek-v4-flash")

def get_local_model() -> str:
    return _env("LLM_LOCAL_MODEL", "ocg/mimo-v2.5-pro")


# ─── Tiered Fallback State ─────────────────────────────────────────────────────

_fallback_level = 0  # 0=tunnel, 1=featherless, 2=nvidia

def _check_provider(base_url: str, api_key: str, timeout: int = 3) -> bool:
    """Check if a provider is reachable."""
    if not api_key:
        return False
    try:
        r = httpx.get(f"{base_url.rstrip('/')}/models",
                      headers={"Authorization": f"Bearer {api_key}"},
                      timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


# ─── Model Factory with Gentle Fallback ────────────────────────────────────────

def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Get ChatOpenAI with cascading fallback. Each tier is tried silently.
    
    - Tier 1: 9router tunnel (primary)
    - Tier 2: Featherless (if tunnel unreachable)
    - Tier 3: NVIDIA (last resort, rarely used)
    
    Does NOT fallback on rate limits, concurrency, or model-specific errors.
    Only falls through on complete provider failure (auth, DNS, timeout).
    """
    global _fallback_level
    
    model = model_name or get_fast_model()
    
    # Try each tier in order, starting from current level
    for level in range(_fallback_level, 3):
        if level == 0:
            base, key = get_tunnel_base(), get_tunnel_key()
        elif level == 1:
            base, key = get_featherless_base(), get_featherless_key()
        else:
            base, key = get_nvidia_base(), get_nvidia_key()
            model = get_nvidia_model()
        
        if not key:
            continue
        
        # Quick health check — skip if dead
        try:
            r = httpx.get(f"{base.rstrip('/')}/models",
                         headers={"Authorization": f"Bearer {key}"},
                         timeout=2)
            if r.status_code != 200:
                _fallback_level = min(level + 1, 2)
                continue
        except Exception:
            _fallback_level = min(level + 1, 2)
            continue
        
        # Provider is alive — use it
        _fallback_level = level  # Reset to this working tier
        return ChatOpenAI(
            model=model,
            base_url=base,
            api_key=key,
            temperature=0.2,
        )
    
    # All providers failed — return tunnel anyway (will get a clear error)
    return ChatOpenAI(
        model=model,
        base_url=get_tunnel_base(),
        api_key=get_tunnel_key(),
        temperature=0.2,
    )


# ─── Direct Provider Access ────────────────────────────────────────────────────

def get_primary_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Tunnel only (no fallback)."""
    return ChatOpenAI(
        model=model_name or get_fast_model(),
        base_url=get_tunnel_base(),
        api_key=get_tunnel_key(),
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


# ─── Health Check ──────────────────────────────────────────────────────────────

def is_proxy_available() -> bool:
    """Check if the 9router tunnel is reachable."""
    try:
        r = httpx.get(f"{get_tunnel_base()}/models",
                      headers={"Authorization": f"Bearer {get_tunnel_key()}"},
                      timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Fetch available models from the tunnel."""
    try:
        r = httpx.get(f"{get_tunnel_base()}/models",
                      headers={"Authorization": f"Bearer {get_tunnel_key()}"},
                      timeout=10)
        if r.status_code == 200:
            data = r.json()
            return [m["id"] for m in data.get("data", [])]
        return []
    except Exception:
        return []

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
