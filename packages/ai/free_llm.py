"""
RealtyAI — Guerrilla Free-LLM Pool ("Keep Us Coding" gateway).

A self-healing pool of *free* OpenAI-compatible LLM endpoints. The
ResilientLLM wrapper rotates across endpoints on ANY failure (timeout, 429,
5xx, auth, quota) and applies a quota-aware cooldown so we never hammer a
struggling upstream.

Guerrilla strategy (see FREETIER.md):
  1. MAX OUT 9router first. It is our self-hosted multi-upstream proxy that
     aggregates ~80 free models (DeepSeek, NVIDIA, OpenAI-proxied, opencode-go
     `ocg/`, Cloudflare `cf/`). We route across its *specific* upstreams with
     per-upstream cooldowns parsed from 9router's own "reset after Xm" errors,
     so we spread load instead of blindly burning `combo_test` slots on dead
     upstreams.
  2. Fall back to the broader free pool (Groq, OpenRouter, NVIDIA, ...) only
     when 9router is cooling.
  3. opencode-zen + the keyless local 9router proxy are always-available anchors.
  4. Every keyed provider accepts MULTIPLE keys (comma/newline separated) so one
     config fans out into N independent budget slots — multiplied free quota.

To add a provider: append a dict to FREE_PROVIDERS below. To add 9router
upstreams: append to NINEROUTER_UPSTREAMS.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from free_tier import (
    UsageStore,
    get_store,
    split_keys,
    parse_reset_seconds,
    is_quota_error,
)
from token_saver import (
    tier_from_model,
    upstreams_for_tier,
    MAX_TOKENS_FAST,
    MAX_TOKENS_COMPLEX,
)

logger = logging.getLogger(__name__)


# ─── 9router upstreams we actively rotate across ─────────────────────────────
# Curated for coding quality + free-quota headroom. `combo_test` is the
# self-healing aggregate (used as a catch-all when specifics are cooling).
NINEROUTER_UPSTREAMS = [
    "combo_test",                      # self-healing round-robin across all upstreams
    "ocg/kimi-k2.7-code",              # opencode-go coding specialist
    "ds/deepseek-reasoner",            # deepseek reasoning
    "ds/deepseek-chat",                # deepseek chat
    "nvidia/kimi-k2.6",                # NVIDIA kimi
    "nvidia/z-ai/glm-5.2",             # NVIDIA glm
    "openai/gpt-5.4-nano",             # cheap + strong
    "ocg/qwen3.7-max",                 # opencode-go qwen
    "cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast",  # Cloudflare llama
]


# ─── Free Provider Registry ───────────────────────────────────────────────────
# Order = priority. opencode-zen is primary (keyless, always available).
# 9router and other providers are fallbacks.
FREE_PROVIDERS = [
    {
        "name": "opencode-zen",
        "base": "https://opencode.ai/zen/v1",
        "key_env": "LLM_API_KEY",          # optional; zen works keyless
        "model": "deepseek-v4-flash-free",
        "keyless": True,
        "note": "Primary free tier (Novita upstream). No key required.",
    },
    {
        "name": "9router",
        # Keyless local proxy (fastest, always up where the proxy runs).
        "local_base": "http://localhost:20128/v1",
        # Keyed public Cloudflare tunnel.
        "base": os.environ.get("NINEROUTER_BASE_URL", "https://r9tgp4c.abc-tunnel.us/v1"),
        "key_env": "NINEROUTER_API_KEY",
        "model": "combo_test",
        "models": NINEROUTER_UPSTREAMS,
        "keyless": False,
        "key_optional": True,   # include even with no key (local :20128 is keyless)
        "note": "Self-hosted multi-upstream proxy. Fallback. Keyless on localhost:20128; keyed on the tunnel.",
    },
    {
        "name": "nvidia",
        "base": "https://integrate.api.nvidia.com/v1",
        "key_env": "LLM_FALLBACK3_API_KEY",
        "model": "meta/llama-3.1-8b-instruct",
        "keyless": False,
        "note": "NVIDIA free inference. Key: developers.nvidia.com",
    },
    {
        "name": "groq",
        "base": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
        "keyless": False,
        "note": "Groq free tier. Multiple keys = multiplied quota. Key: console.groq.com",
    },
    {
        "name": "openrouter",
        "base": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "keyless": False,
        "note": "OpenRouter free models (':free' suffix). Key: openrouter.ai/keys",
    },
    {
        "name": "deepinfra",
        "base": "https://api.deepinfra.com/v1/openai",
        "key_env": "DEEPINFRA_API_KEY",
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "keyless": False,
        "note": "DeepInfra free tier. Key: deepinfra.com",
    },
    {
        "name": "huggingface",
        "base": "https://api-inference.huggingface.co/v1",
        "key_env": "HF_API_KEY",
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "keyless": False,
        "note": "HF serverless inference. Key: huggingface.co/settings/tokens",
    },
    {
        "name": "github-models",
        "base": "https://models.inference.ai.azure.com",
        "key_env": "GITHUB_TOKEN",
        "model": "meta-llama/Llama-3.1-70b-Instruct",
        "keyless": False,
        "note": "GitHub Models (free for GH users). Key: github.com/settings/tokens",
    },
    {
        "name": "sambanova",
        "base": "https://api.sambanova.ai/v1",
        "key_env": "SAMBANOVA_API_KEY",
        "model": "Meta-Llama-3.3-70B-Instruct",
        "keyless": False,
        "note": "SambaNova free tier. Key: cloud.sambanova.ai",
    },
    {
        "name": "together",
        "base": "https://api.together.xyz/v1",
        "key_env": "TOGETHER_API_KEY",
        "model": "meta-llama/Llama-3.3-8B-Instruct-Turbo",
        "keyless": False,
        "note": "Together free credits. Key: api.together.xyz/settings/api-keys",
    },
    {
        "name": "fireworks",
        "base": "https://api.fireworks.ai/inference/v1",
        "key_env": "FIREWORKS_API_KEY",
        "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
        "keyless": False,
        "note": "Fireworks free credits. Key: fireworks.ai/api-keys",
    },
]

# Cooldown (seconds) before a failed endpoint is retried (when no timer parsed).
DEFAULT_COOLDOWN = 60
# Cap on chat completion time before we treat an endpoint as "down" and rotate.
INVOKE_TIMEOUT = 90


def get_free_providers() -> list[dict]:
    """Return the active provider list (deep-copied so callers can mutate)."""
    return [dict(p) for p in FREE_PROVIDERS]


def _resolve_key(p: dict) -> str:
    return os.environ.get(p.get("key_env", ""), "") or ""


def _enabled_providers() -> list[dict]:
    out = []
    for p in get_free_providers():
        key = _resolve_key(p)
        if p.get("keyless") or p.get("key_optional"):
            out.append(p)
        elif key:
            out.append(p)
    return out


def _expand_endpoints(tier: str = "fast") -> list[dict]:
    """Flatten providers -> concrete endpoints.

    Each endpoint = (provider, model, base, key, key_index). We fan out across:
      * multiple bases  (9router local keyless + keyed tunnel)
      * multiple keys   (comma/newline separated -> multiplied quota)
      * multiple models (9router specific upstreams, filtered by `tier`)
    """
    endpoints = []
    for p in _enabled_providers():
        name = p["name"]
        key = _resolve_key(p)
        keyless = bool(p.get("keyless"))
        key_optional = bool(p.get("key_optional"))

        # Bases: optional keyless local proxy + the primary base.
        bases: list[dict] = []
        if p.get("local_base"):
            bases.append({"url": p["local_base"], "key": "", "keyless": True, "tag": "local"})
        if keyless or key_optional or key:
            bases.append({"url": p["base"], "key": key, "keyless": keyless, "tag": "main"})

        # Keys: split multi-key, or a single empty key for keyless/optional.
        if keyless or key_optional:
            keys = [""]
        else:
            keys = split_keys(key)
        if not keys:
            continue

        # 9router upstreams are filtered by tier so trivial work hits tiny
        # models (few tokens, fast) and only hard tasks hit reasoners.
        if name == "9router":
            models = upstreams_for_tier(tier)
        else:
            models = p.get("models") or [p["model"]]

        for bi, b in enumerate(bases):
            for ki, k in enumerate(keys):
                for model in models:
                    endpoints.append({
                        "provider": name,
                        "model": model,
                        "base": b["url"],
                        "key": k,
                        "keyless": b["keyless"],
                        "key_index": ki,
                        "tag": b["tag"],
                        "endpoint_id": f"{name}:{model}@{b['tag']}#{ki}",
                        "note": p.get("note", ""),
                    })
    return endpoints


class ResilientLLM:
    """ChatOpenAI-compatible wrapper that rotates across free endpoints.

    Usage mirrors ChatOpenAI:
        llm = ResilientLLM()
        llm_with_tools = llm.bind_tools(tools)
        msg = llm.invoke(messages)

    On any invocation failure it cools the endpoint down (using 9router's own
    reset timer when available) and retries the next healthy endpoint. Budgets
    are enforced per (provider, key) so we never blow a free daily limit.
    `last_provider` records which endpoint actually answered (for telemetry).
    """

    def __init__(
        self,
        providers: Optional[list[dict]] = None,
        model_name: str = "combo_test",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        tier: str = "fast",
        prefer_local: bool = False,
    ):
        self.model_name = model_name
        self.temperature = temperature
        # Tier sets a sensible token cap unless the caller overrides.
        self.max_tokens = max_tokens or (
            MAX_TOKENS_COMPLEX if tier == "complex" else MAX_TOKENS_FAST
        )
        self._tier = tier
        self._prefer_local = prefer_local
        self._tools = None
        self._endpoints = _expand_endpoints(tier)
        self._clients: dict[str, Optional[ChatOpenAI]] = {}
        self._health: dict[str, float] = {}   # endpoint_id -> cooldown_until
        self._cursor = 0
        self._store: UsageStore = get_store()
        self.last_provider: Optional[str] = None
        if not self._endpoints:
            logger.warning("ResilientLLM: no free endpoints enabled!")

    # ── internal helpers ──────────────────────────────────────────────────

    def _build_one(self, ep: dict) -> Optional[ChatOpenAI]:
        try:
            llm = ChatOpenAI(
                model=ep["model"],
                base_url=ep["base"],
                api_key=ep["key"] or "sk-noauth",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=INVOKE_TIMEOUT,
                max_retries=0,   # we do our own fallback across endpoints
            )
            if self._tools:
                llm = llm.bind_tools(self._tools)
            return llm
        except Exception as e:
            logger.warning("ResilientLLM: failed to build %s: %s", ep["endpoint_id"], e)
            return None

    def _client(self, ep: dict) -> Optional[ChatOpenAI]:
        c = self._clients.get(ep["endpoint_id"])
        if c is None and ep["endpoint_id"] not in self._clients:
            c = self._build_one(ep)
            self._clients[ep["endpoint_id"]] = c
        return c

    def _healthy(self, ep: dict, now: float) -> bool:
        cool = self._health.get(ep["endpoint_id"], 0.0)
        if now < cool:
            return False
        # Budget guard (soft — we still allow as a last resort below).
        if self._store.is_exhausted(ep["provider"], ep["key_index"]):
            return False
        return self._client(ep) is not None

    def _next(self, allow_exhausted: bool = False):
        """Yield the next healthy (endpoint, llm), advancing the cursor.

        When `prefer_local` is set (privacy-sensitive tasks), local 9router
        endpoints are tried first; only if none are healthy do we spill to the
        tunnel.
        """
        n = len(self._endpoints)
        now = time.time()

        def candidate(ep, local_only: bool) -> bool:
            if local_only and ep["tag"] != "local":
                return False
            if not allow_exhausted and self._store.is_exhausted(ep["provider"], ep["key_index"]):
                return False
            if now < self._health.get(ep["endpoint_id"], 0.0):
                return False
            return self._client(ep) is not None

        # Pass 1: respect prefer_local if it yields anything.
        if self._prefer_local:
            for _ in range(n):
                ep = self._endpoints[self._cursor % n]
                self._cursor = (self._cursor + 1) % n
                if candidate(ep, local_only=True):
                    return ep, self._client(ep)
        # Pass 2: any healthy endpoint.
        for _ in range(n):
            ep = self._endpoints[self._cursor % n]
            self._cursor = (self._cursor + 1) % n
            if candidate(ep, local_only=False):
                return ep, self._client(ep)
        return None, None

    def _mark_down(self, ep: dict, seconds: int = DEFAULT_COOLDOWN, err: str = ""):
        # If 9router told us exactly when the upstream resets, use that.
        if seconds == DEFAULT_COOLDOWN:
            parsed = parse_reset_seconds(err)
            if parsed:
                seconds = min(parsed + 5, 6 * 3600)  # cap to avoid permanent park
        self._health[ep["endpoint_id"]] = time.time() + seconds
        # Also park just this upstream (not the whole proxy) in the usage store.
        self._store.set_cooldown(ep["endpoint_id"], seconds)

    # ── ChatOpenAI-compatible interface ───────────────────────────────────

    def bind_tools(self, tools):
        self._tools = tools
        for cid, c in self._clients.items():
            if c is not None:
                self._clients[cid] = c.bind_tools(tools)
        return self

    def invoke(self, messages, **kwargs):
        last_err = None
        n = len(self._endpoints)
        for _ in range(n):
            ep, llm = self._next()
            if llm is None:
                ep, llm = self._next(allow_exhausted=True)
            if llm is None:
                break
            try:
                result = llm.invoke(messages, **kwargs)
                self.last_provider = ep["endpoint_id"]
                self._store.record(ep["provider"], ep["key_index"], requests=1,
                                   tokens=max(1, len(str(getattr(result, "content", ""))) // 4))
                logger.info("ResilientLLM: served by %s", ep["endpoint_id"])
                return result
            except Exception as e:
                err = str(e)
                logger.warning("ResilientLLM: %s failed: %s", ep["endpoint_id"], err[:160])
                cool = DEFAULT_COOLDOWN
                if is_quota_error(err):
                    cool = DEFAULT_COOLDOWN
                self._mark_down(ep, cool, err)
                last_err = e
        raise last_err or RuntimeError("All free LLM endpoints failed")

    async def ainvoke(self, messages, **kwargs):
        last_err = None
        n = len(self._endpoints)
        for _ in range(n):
            ep, llm = self._next()
            if llm is None:
                ep, llm = self._next(allow_exhausted=True)
            if llm is None:
                break
            try:
                result = await llm.ainvoke(messages, **kwargs)
                self.last_provider = ep["endpoint_id"]
                self._store.record(ep["provider"], ep["key_index"], requests=1,
                                   tokens=max(1, len(str(getattr(result, "content", ""))) // 4))
                logger.info("ResilientLLM: served by %s", ep["endpoint_id"])
                return result
            except Exception as e:
                err = str(e)
                logger.warning("ResilientLLM: %s failed: %s", ep["endpoint_id"], err[:160])
                self._mark_down(ep, DEFAULT_COOLDOWN, err)
                last_err = e
        raise last_err or RuntimeError("All free LLM endpoints failed")

    def status(self) -> dict:
        """Diagnostics: endpoints, cooldowns, budgets, last provider."""
        now = time.time()
        endpoints = []
        for ep in self._endpoints:
            endpoints.append({
                "id": ep["endpoint_id"],
                "provider": ep["provider"],
                "model": ep["model"],
                "tag": ep["tag"],
                "cooled_down": now < self._health.get(ep["endpoint_id"], 0.0),
                "budget": self._store.remaining(ep["provider"], ep["key_index"]),
            })
        return {
            "endpoint_count": len(self._endpoints),
            "last_provider": self.last_provider,
            "endpoints": endpoints,
            "usage": self._store.snapshot(),
        }


def build_resilient_llm(
    model_name: str = "combo_test",
    tier: Optional[str] = None,
    prefer_local: bool = False,
    **kwargs,
) -> ResilientLLM:
    """Convenience factory used by the Athena agent (guerrilla primary).

    `tier` defaults from the model-name hint (premium/reasoning/local ->
    'complex') so callers can just pass the model name they already compute.
    """
    if tier is None:
        tier = tier_from_model(model_name)
    return ResilientLLM(
        model_name=model_name,
        tier=tier,
        prefer_local=prefer_local,
        **kwargs,
    )


# Backwards-compatible alias.
build_guerrilla_llm = build_resilient_llm
