"""
RealtyAI — Model Gateway with 4-Tier Cascading Fallback.

Tier 0 (primary):  OpenCode Zen (free tier, via opencode.ai)
Tier 1:             9router tunnel proxy (ocg/ models via cloudflared)
Tier 2:             Featherless.ai (paid, fast)
Tier 3:             NVIDIA API (last resort)

Each level falls through ONLY on total failure (timeout, auth, down).
Rate limits and concurrency caps do NOT trigger fallback — they retry.
"""
import os
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
import httpx

logger = logging.getLogger(__name__)


# ─── Config ───────────────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# Tier configs — populated at call time from env vars
TIERS = [
    {  # 0: OpenCode Zen
        "base": lambda: _env("LLM_API_BASE", "https://opencode.ai/zen/v1"),
        "key":  lambda: _env("LLM_API_KEY", ""),
        "model": lambda: _env("LLM_DEFAULT_MODEL", "hy3-free"),
    },
    {  # 1: 9router tunnel
        "base": lambda: _env("LLM_FALLBACK_API_BASE", ""),
        "key":  lambda: _env("LLM_FALLBACK_API_KEY", ""),
        "model": lambda: _env("LLM_FALLBACK_MODEL", "ocg/kimi-k2.6"),
    },
    {  # 2: Featherless
        "base": lambda: _env("LLM_FALLBACK2_API_BASE", "https://api.featherless.ai/v1"),
        "key":  lambda: _env("LLM_FALLBACK2_API_KEY", ""),
        "model": lambda: _env("LLM_FALLBACK2_MODEL", "Qwen/Qwen3-4B-Instruct-2507"),
    },
    {  # 3: NVIDIA
        "base": lambda: _env("LLM_FALLBACK3_API_BASE", "https://integrate.api.nvidia.com/v1"),
        "key":  lambda: _env("LLM_FALLBACK3_API_KEY", ""),
        "model": lambda: _env("LLM_FALLBACK3_MODEL", "meta/llama-3.1-8b-instruct"),
    },
]

MAX_TIER = len(TIERS) - 1

# Model name overrides
def get_fast_model() -> str:
    return _env("LLM_DEFAULT_MODEL", "hy3-free")

def get_premium_model() -> str:
    return _env("LLM_PREMIUM_MODEL", "hy3-free")

def get_local_model() -> str:
    return _env("LLM_LOCAL_MODEL", "hy3-free")


# ─── Tiered Fallback State ─────────────────────────────────────────────────────

_fallback_level = 0  # Start at tier 0

def reset_fallback():
    """Reset fallback to tier 0 (after providers recover)."""
    global _fallback_level
    _fallback_level = 0


# ─── Model Factory with Gentle Fallback ────────────────────────────────────────

def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Get ChatOpenAI with cascading fallback across all configured tiers.
    
    Tries tiers starting from `_fallback_level`. Falls through on total
    provider failure only. Returns the best available model.
    """
    global _fallback_level

    model = model_name or get_fast_model()

    for level in range(_fallback_level, MAX_TIER + 1):
        tier = TIERS[level]
        base = tier["base"]()
        key = tier["key"]()
        m = tier["model"]() if level > 0 else model  # Use original model for tier 0

        if not base or not key:
            _fallback_level = min(level + 1, MAX_TIER)
            continue

        # Quick health check — skip if completely dead
        try:
            r = httpx.get(f"{base.rstrip('/')}/models",
                         headers={"Authorization": f"Bearer {key}"},
                         timeout=2)
            if r.status_code != 200:
                _fallback_level = min(level + 1, MAX_TIER)
                continue
        except Exception:
            _fallback_level = min(level + 1, MAX_TIER)
            continue

        # Provider is alive — use it and remember this tier
        _fallback_level = level
        return ChatOpenAI(
            model=m,
            base_url=base,
            api_key=key,
            temperature=0.2,
        )

    # All providers failed — return tier 0 anyway (will get a clear error)
    return ChatOpenAI(
        model=model,
        base_url=TIERS[0]["base"](),
        api_key=TIERS[0]["key"](),
        temperature=0.2,
    )


# ─── Direct Provider Access ────────────────────────────────────────────────────

def get_primary_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Tier 0 only (no fallback)."""
    tier = TIERS[0]
    return ChatOpenAI(
        model=model_name or get_fast_model(),
        base_url=tier["base"](),
        api_key=tier["key"](),
        temperature=0.2,
    )


def get_fallback_model() -> ChatOpenAI:
    """NVIDIA only (last tier, no fallback)."""
    tier = TIERS[MAX_TIER]
    return ChatOpenAI(
        model=tier["model"](),
        base_url=tier["base"](),
        api_key=tier["key"](),
        temperature=0.2,
    )


# ─── Health Checks ─────────────────────────────────────────────────────────────

def is_proxy_available() -> bool:
    """Check if tier 0 (primary API) is reachable."""
    tier = TIERS[0]
    try:
        r = httpx.get(
            f"{tier['base']()}/models",
            headers={"Authorization": f"Bearer {tier['key']()}"},
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Fetch available models from tier 0."""
    tier = TIERS[0]
    try:
        r = httpx.get(
            f"{tier['base']()}/models",
            headers={"Authorization": f"Bearer {tier['key']()}"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            return [m["id"] for m in data.get("data", [])]
        return []
    except Exception:
        return []
