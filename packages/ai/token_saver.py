"""
RealtyAI — Token-Saver (stretch free quota by spending fewer tokens/call).

Token cost per call = input (system prompt + tool schemas + history) + output
(max_tokens cap + model verbosity). We attack all three:

  1. COMPACT_SYSTEM_PROMPT — caveman-lite system prompt (~50 tok vs ~250).
  2. FAST/COMPLEX upstream tiers — trivial lookups hit tiny models
     (gpt-5.4-nano / deepseek-chat), deep reasoning hits a reasoner. Routing
     simple work to small models is the single biggest per-call saving.
  3. MAX_TOKENS presets — 1024 for fast, 2048 for complex (was 4096).
  4. truncate_messages() — window long histories before they bloat input.
  5. TERSE_HINT — instructs the model to answer short, saving output tokens.

Everything is opt-out via env: TOKEN_SAVER=0 restores the verbose prompt and
the old 4096 cap.
"""
from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)


def token_saver_on() -> bool:
    return os.environ.get("TOKEN_SAVER", "1") != "0"


# ─── Compact system prompt (caveman-lite) ────────────────────────────────────
# Keeps 100% of the meaning, drops articles/filler/hedging. Sent on EVERY call,
# so this is the highest-leverage compression in the system.
COMPACT_SYSTEM_PROMPT = (
    "RealtyAI: assistant for real estate agents. Help with leads, listings, "
    "client comms, biz insights. Use tools to fetch data. Lead with actionable "
    "info. If unsure, say so — don't guess. Professional, warm, terse. Reply "
    "brief unless detail requested."
)

TERSE_HINT = " Be concise. Minimal words."

# Verbose original, kept for opt-out / reference.
VERBOSE_SYSTEM_PROMPT = (
    "You are RealtyAI, an AI assistant for professional real estate agents.\n\n"
    "You help agents manage their business more effectively. Your capabilities include:\n"
    "- Lead management: Review leads, identify hot prospects, track status\n"
    "- Property listings: Search active listings, answer questions about properties\n"
    "- Client communication: Draft follow-up emails, listing alerts\n"
    "- Business insights: Summarize lead activity, identify priorities\n\n"
    "## How you work\n"
    "1. When the agent asks a question, use your tools to look up business data.\n"
    "2. Present information clearly and concisely — agents are busy.\n"
    "3. Always lead with the most important/actionable information.\n"
    "4. If you don't know something, say so rather than guessing.\n\n"
    "## Tone\n"
    "Professional, warm, and efficient. Like a great assistant who respects your time.\n"
    "Keep responses brief unless the agent asks for detail."
)


def system_prompt() -> str:
    if token_saver_on():
        return COMPACT_SYSTEM_PROMPT + (TERSE_HINT if token_saver_on() else "")
    return VERBOSE_SYSTEM_PROMPT


# ─── 9router upstream tiers (model-size aware routing) ────────────────────────
# FAST: tiny/cheap models — few tokens, low latency. Use for lookups + short answers.
FAST_UPSTREAMS = [
    "openai/gpt-5.4-nano",
    "ds/deepseek-chat",
    "nvidia/z-ai/glm-5.2",
    "cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "ocg/qwen3.7-max",
]
# COMPLEX: reasoning / coding models — bigger, slower, pricier in quota. Use only
# when the task needs it (analysis, drafting, negotiation).
COMPLEX_UPSTREAMS = [
    "ds/deepseek-reasoner",
    "ocg/kimi-k2.7-code",
    "nvidia/kimi-k2.6",
    "combo_test",
]

# max_tokens presets by tier (was a flat 4096).
MAX_TOKENS_FAST = int(os.environ.get("FT_MAX_TOKENS_FAST", "1024"))
MAX_TOKENS_COMPLEX = int(os.environ.get("FT_MAX_TOKENS_COMPLEX", "2048"))


def tier_from_model(model_name: str) -> str:
    """Map a model-name hint to a routing tier.

    'premium' / 'reasoning' / 'local' -> 'complex'; everything else -> 'fast'.
    """
    n = (model_name or "").lower()
    if any(k in n for k in ("premium", "reasoning", "local", "complex")):
        return "complex"
    return "fast"


def upstreams_for_tier(tier: str) -> list[str]:
    if tier == "complex":
        return COMPLEX_UPSTREAMS
    return FAST_UPSTREAMS


# ─── History windowing ────────────────────────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Good enough for budgeting."""
    return max(1, len(text or "") // 4)


def truncate_messages(messages: list, max_input_tokens: int = 3000) -> list:
    """Keep the system message + the most recent messages under a token budget.

    Prevents long conversation histories from bloating every follow-up call.
    System/prompt messages (role == 'system') are always retained.
    """
    if not messages:
        return messages
    kept = []
    budget = max_input_tokens
    # Preserve any system message first.
    for m in messages:
        if getattr(m, "role", None) == "system" or getattr(m, "type", None) == "system":
            kept.append(m)
    # Then walk from the end, adding messages until the budget is exhausted.
    for m in reversed(messages):
        if m in kept:
            continue
        content = getattr(m, "content", "") or ""
        cost = estimate_tokens(content) if isinstance(content, str) else 200
        if budget - cost < 0 and kept:
            break
        kept.append(m)
        budget -= cost
    # Restore original order (system first, then chronological recent).
    ordered = [m for m in messages if m in kept]
    return ordered
