"""
RealtyAI — Free LLM Provider Pool ("Keep Us Coding" gateway).

A self-healing pool of *free* OpenAI-compatible LLM providers. The
ResilientLLM wrapper rotates across providers on ANY failure (timeout,
429 rate-limit, 5xx, auth error) and applies a short cooldown to dead
providers so we never hammer a struggling endpoint. With 10 free
providers wired in, Athena always has somewhere to fall through.

Keyless providers (e.g. OpenCode Zen) work with no API key. The rest are
env-gated: set the matching *_API_KEY and they join the rotation
automatically — no code changes needed.

To add a provider: append a dict to FREE_PROVIDERS below.
"""
import os
import time
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


# ─── Free Provider Registry ───────────────────────────────────────────────────
# Every entry is a FREE, OpenAI-compatible endpoint. `keyless` providers need no
# key. `key_env` is the environment variable that holds the API key (if any).
# `model` is the default free model for that provider.
FREE_PROVIDERS = [
    {
        "name": "opencode-zen",
        "base": "https://opencode.ai/zen/v1",
        "key_env": "LLM_API_KEY",          # optional; zen works keyless
        "model": "hy3-free",
        "keyless": True,
        "note": "Primary free tier (Novita upstream). No key required.",
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
        "note": "Groq free tier. Key: console.groq.com",
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

# Cooldown (seconds) before a failed provider is retried.
DEFAULT_COOLDOWN = 60
# Cap on chat completion time before we treat a provider as "down" and rotate.
INVOKE_TIMEOUT = 90


def get_free_providers() -> list[dict]:
    """Return the active provider list (deep-copied so callers can mutate)."""
    return [dict(p) for p in FREE_PROVIDERS]


def _resolve_key(p: dict) -> str:
    if p.get("keyless"):
        return os.environ.get(p["key_env"], "") or ""
    return os.environ.get(p["key_env"], "")


def _enabled_providers() -> list[dict]:
    out = []
    for p in get_free_providers():
        if p.get("keyless"):
            out.append(p)
        elif _resolve_key(p):
            out.append(p)
    return out


class ResilientLLM:
    """ChatOpenAI-compatible wrapper that rotates across free providers.

    Usage mirrors ChatOpenAI:
        llm = ResilientLLM()
        llm_with_tools = llm.bind_tools(tools)
        msg = llm.invoke(messages)

    On any invocation failure it marks the provider unhealthy (cooldown) and
    retries with the next healthy provider. `last_provider` records which
    provider actually answered (useful for telemetry).
    """

    def __init__(
        self,
        providers: Optional[list[dict]] = None,
        model_name: str = "hy3-free",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._tools = None
        self._providers = providers or _enabled_providers()
        self._health: dict[str, float] = {}   # name -> cooldown_until (epoch)
        self._cursor = 0
        self.last_provider: Optional[str] = None
        if not self._providers:
            logger.warning("ResilientLLM: no free providers enabled!")

    # ── internal helpers ──────────────────────────────────────────────────

    def _build_one(self, p: dict) -> Optional[ChatOpenAI]:
        key = _resolve_key(p)
        if not p.get("keyless") and not key:
            return None
        try:
            llm = ChatOpenAI(
                model=p["model"],
                base_url=p["base"],
                api_key=key or "sk-noauth",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=INVOKE_TIMEOUT,
                max_retries=0,   # we do our own fallback across providers
            )
            if self._tools:
                llm = llm.bind_tools(self._tools)
            return llm
        except Exception as e:
            logger.warning("ResilientLLM: failed to build %s: %s", p["name"], e)
            return None

    def _next(self):
        """Yield the next healthy (provider, llm), advancing the cursor."""
        n = len(self._providers)
        now = time.time()
        for _ in range(n):
            p = self._providers[self._cursor % n]
            self._cursor = (self._cursor + 1) % n
            cooldown = self._health.get(p["name"])
            if cooldown and now < cooldown:
                continue
            llm = self._build_one(p)
            if llm is None:
                continue
            return p, llm
        return None, None

    def _mark_down(self, name: str, seconds: int = DEFAULT_COOLDOWN):
        self._health[name] = time.time() + seconds

    # ── ChatOpenAI-compatible interface ───────────────────────────────────

    def bind_tools(self, tools):
        self._tools = tools
        return self

    def invoke(self, messages, **kwargs):
        last_err = None
        for _ in range(len(self._providers)):
            p, llm = self._next()
            if llm is None:
                continue
            try:
                result = llm.invoke(messages, **kwargs)
                self.last_provider = p["name"]
                logger.info("ResilientLLM: served by %s", p["name"])
                return result
            except Exception as e:
                logger.warning("ResilientLLM: %s failed: %s", p["name"], e)
                self._mark_down(p["name"])
                last_err = e
        # Absolute last resort: hammer opencode-zen directly
        try:
            last = ChatOpenAI(
                model="hy3-free",
                base_url="https://opencode.ai/zen/v1",
                api_key=os.environ.get("LLM_API_KEY", "") or "sk-noauth",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=INVOKE_TIMEOUT,
            )
            if self._tools:
                last = last.bind_tools(self._tools)
            result = last.invoke(messages, **kwargs)
            self.last_provider = "opencode-zen"
            return result
        except Exception:
            pass
        raise last_err or RuntimeError("All free LLM providers failed")

    async def ainvoke(self, messages, **kwargs):
        last_err = None
        for _ in range(len(self._providers)):
            p, llm = self._next()
            if llm is None:
                continue
            try:
                result = await llm.ainvoke(messages, **kwargs)
                self.last_provider = p["name"]
                logger.info("ResilientLLM: served by %s", p["name"])
                return result
            except Exception as e:
                logger.warning("ResilientLLM: %s failed: %s", p["name"], e)
                self._mark_down(p["name"])
                last_err = e
        raise last_err or RuntimeError("All free LLM providers failed")

    def status(self) -> dict:
        """Diagnostics: which providers are enabled / cooled-down."""
        now = time.time()
        return {
            "enabled": [p["name"] for p in self._providers],
            "cooled_down": [
                name for name, until in self._health.items() if now < until
            ],
            "last_provider": self.last_provider,
        }


def build_resilient_llm(model_name: str = "hy3-free", **kwargs) -> ResilientLLM:
    """Convenience factory used by the Athena agent."""
    return ResilientLLM(model_name=model_name, **kwargs)
