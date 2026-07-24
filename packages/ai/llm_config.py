"""
RealtyAI — Model Gateway with 5-Tier Cascading Fallback.

Tier 0 (primary):  OpenCode Zen (free tier, via opencode.ai)
Tier 1:             9router tunnel proxy (ocg/ models via cloudflared)
Tier 2:             Featherless.ai (paid, fast)
Tier 3:             NVIDIA API (free last-resort)
Tier 4:             Groq (free tier, fast) — only used if GROQ_API_KEY set

Free providers in the chain: OpenCode Zen (0), NVIDIA (3), Groq (4).
Each level falls through ONLY on total failure (timeout, auth, down).
Rate limits and concurrency caps do NOT trigger fallback — they retry.
"""
import os
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
import httpx

# Guerrilla free-LLM pool (9router-first, quota-aware). Imported lazily so a
# missing dep never breaks the legacy tiered path below.
try:
    from free_llm import ResilientLLM, build_resilient_llm
    from token_saver import tier_from_model
    _HAVE_GUERRILLA = True
except Exception:  # pragma: no cover
    _HAVE_GUERRILLA = False

logger = logging.getLogger(__name__)


# ─── Config ───────────────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# Tier configs — populated at call time from env vars
TIERS = [
    {  # 0: OpenCode Zen
        "base": lambda: _env("LLM_API_BASE", "https://opencode.ai/zen/v1"),
        "key":  lambda: _env("LLM_API_KEY", ""),
        "model": lambda: _env("LLM_DEFAULT_MODEL", "deepseek-v4-flash-free"),
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
    {  # 4: Groq (free tier) — only used if GROQ_API_KEY is set
        "base": lambda: _env("LLM_FALLBACK4_API_BASE", "https://api.groq.com/openai/v1"),
        "key":  lambda: _env("GROQ_API_KEY", ""),
        "model": lambda: _env("LLM_FALLBACK4_MODEL", "llama-3.3-70b-versatile"),
    },
]

MAX_TIER = len(TIERS) - 1

# Model name overrides
def get_fast_model() -> str:
    return _env("LLM_DEFAULT_MODEL", "deepseek-v4-flash-free")

def get_premium_model() -> str:
    return _env("LLM_PREMIUM_MODEL", "mimo-v2.5-free")

def get_local_model() -> str:
    return _env("LLM_LOCAL_MODEL", "deepseek-v4-flash-free")


# ─── Tiered Fallback State ─────────────────────────────────────────────────────

_fallback_level = 0  # Start at tier 0

def reset_fallback():
    """Reset fallback to tier 0 (after providers recover)."""
    global _fallback_level
    _fallback_level = 0


# ─── Model Factory with Gentle Fallback ────────────────────────────────────────

def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Get a model with the guerrilla free-LLM pool as primary.

    When the guerrilla pool is available (env GUERRILLA_LLM != '0'), we return
    a ResilientLLM that maxes out 9router and falls back across all free
    providers — $0 spend. Otherwise we fall back to the legacy tiered
    ChatOpenAI chain so nothing breaks.
    """
    global _fallback_level

    if _HAVE_GUERRILLA and os.environ.get("GUERRILLA_LLM", "1") != "0":
        try:
            name = model_name or get_fast_model()
            # Privacy-sensitive tasks route to the keyless local 9router proxy.
            prefer_local = "local" in name.lower()
            return build_resilient_llm(name, prefer_local=prefer_local)
        except Exception as e:
            logger.warning("Guerrilla pool unavailable (%s); using legacy tiers", e)

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
