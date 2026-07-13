"""
RealtyAI — LiteLLM Model Gateway.

All AI requests flow through LiteLLM proxy at localhost:4000.
The proxy handles routing to the appropriate model based on:
- Task type (private data → local, complex → cloud)
- Model availability
- Cost optimization

Architecture:
    Agent → LiteLLM Proxy (:4000) → Local llama.cpp (:8000)
                                 → Claude (Anthropic)
                                 → GPT (OpenAI)
                                 → Gemini (Google)
"""
import os
from typing import Optional

from langchain_openai import ChatOpenAI
import httpx


# ─── LiteLLM Proxy Config ───────────────────────────────────────────────────

LITELLM_BASE = os.getenv("LLM_API_BASE", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LLM_API_KEY", "anything")

# Model names as defined in infrastructure/litellm/config.yaml
MODEL_FAST = os.getenv("LLM_DEFAULT_MODEL", "fast-model")
MODEL_PREMIUM = os.getenv("LLM_PREMIUM_MODEL", "premium-reasoning")
MODEL_LOCAL = os.getenv("LLM_LOCAL_MODEL", "local-realty-model")


# ─── Model Factory ──────────────────────────────────────────────────────────

def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Get a LangChain ChatOpenAI instance pointed at the LiteLLM proxy.

    The proxy handles all routing — the client just needs to specify
    which model name (as defined in config.yaml) to use.

    Args:
        model_name: Name from the LiteLLM config (fast-model, premium-reasoning,
                   local-realty-model, gemini-flash). If None, uses fast-model.
    """
    return ChatOpenAI(
        model=model_name or MODEL_FAST,
        base_url=f"{LITELLM_BASE.rstrip('/')}/v1",
        api_key=LITELLM_API_KEY,
        temperature=0.2,
    )


# ─── Proxy Health ───────────────────────────────────────────────────────────

def is_proxy_available() -> bool:
    """Check if the LiteLLM proxy is reachable."""
    try:
        r = httpx.get(f"{LITELLM_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Return model names the LiteLLM proxy has configured."""
    try:
        r = httpx.get(
            f"{LITELLM_BASE}/model/list",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("data", [])
        return []
    except Exception:
        return []
