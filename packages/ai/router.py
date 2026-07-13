"""
RealtyAI — Intelligent Model Router.

Routes tasks to the optimal model based on:
- Privacy: sensitive client data → local model (data never leaves)
- Complexity: long/analytical tasks → premium reasoning model
- Speed: simple queries → fast/cheap model
- Cost: default to cheapest capable model

Rules:
1. If task mentions contracts, agreements, financials, or client PII → local model
2. If task is long (>500 chars) or requires deep reasoning → premium model
3. Everything else → fast model

The router doesn't call the LLM itself — it returns the model name
for the caller to use with get_model().
"""
from typing import Optional

from llm_config import get_model, get_local_model, get_premium_model, get_fast_model


# ─── Privacy Keywords ────────────────────────────────────────────────────────

_PRIVATE_KEYWORDS = [
    "contract", "contracts", "agreement", "agreements",
    "disclosure", "disclosures", "inspection", "inspections",
    "financial", "financing", "pre-approval", "preapproval",
    "budget", "mortgage", "closing", "escrow",
    "confidential", "nda", "non-disclosure",
    "client detail", "personal", "private",
    "bank statement", "tax return", "credit score",
]

_COMPLEX_KEYWORDS = [
    "analyze", "analysis", "compare", "comparison",
    "strategy", "recommend", "recommendation",
    "research", "trend", "market analysis",
    "negotiate", "negotiation", "forecast",
    "write a", "draft a", "create a", "generate a",
]


def classify_task(message: str) -> str:
    """Classify a task and return the optimal model name.
    
    Args:
        message: The user's message to the AI.
    
    Returns:
        Model name string: local-realty-model, premium-reasoning, or fast-model.
    """
    msg_lower = message.lower()

    # Rule 1: Private/sensitive data → local model only
    for kw in _PRIVATE_KEYWORDS:
        if kw in msg_lower:
            return get_local_model()

    # Rule 2: Long or complex → premium model
    if len(message) > 500:
        return get_premium_model()
    for kw in _COMPLEX_KEYWORDS:
        if kw in msg_lower:
            return get_premium_model()

    # Rule 3: Everything else → fast model
    return get_fast_model()


def get_routed_model(message: str, override: Optional[str] = None):
    """Get the right model for a message.
    
    Args:
        message: The user's message to classify.
        override: If set, use this model regardless of classification.
    
    Returns:
        A ChatOpenAI instance pointed at the right model through LiteLLM.
    """
    model_name = override or classify_task(message)
    return get_model(model_name)


def get_router_stats() -> dict:
    """Return router configuration for debugging."""
    return {
        "local_model": get_local_model(),
        "premium_model": get_premium_model(),
        "fast_model": get_fast_model(),
        "private_keywords": _PRIVATE_KEYWORDS,
        "complex_keywords": _COMPLEX_KEYWORDS,
        "litellm_base": __import__("os").getenv("LLM_API_BASE", "http://localhost:4000"),
    }
