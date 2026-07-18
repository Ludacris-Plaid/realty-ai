"""
RealtyAI — Guerrilla Free-Tier Governor.

The whole point: keep us coding on a $0 budget.

9router is our unified free-LLM fabric. It exposes ~80 upstreams (DeepSeek,
NVIDIA, OpenAI-proxied, opencode-go `ocg/`, Cloudflare `cf/`) and round-robins
them via `combo_test`. But every upstream has its own quota / balance that
resets on a timer — when one is exhausted 9router returns an error like:

    [opencode-go/minimax-m3] [429]: ... "Monthly usage limit reached.
    R (reset after 4m 56s)"

Blindly hammering `combo_test` wastes slots on dead upstreams. So this module:

  * Tracks a daily request/token BUDGET per provider (and per key, since each
    key is its own quota slot — multiple keys = multiplied free quota).
  * Parses 9router's "reset after Xm Ys" payloads so we cooldown the exact
    upstream for exactly the right window instead of guessing.
  * Persists usage + cooldowns to disk (and Redis when present) so budgets
    survive process restarts.
  * Splits multi-key env vars so one provider config can fan out into N
    independent budget slots.

Design principle: max out 9router first (spread load across its upstreams with
quota-aware cooldowns), fall back to the broader free pool (Groq, OpenRouter,
NVIDIA, ...) only when 9router is cooling, and keep opencode-zen + the keyless
local 9router proxy as always-available anchors.
"""
from __future__ import annotations

import os
import re
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Free-tier daily budgets ─────────────────────────────────────────────────
# Conservative, deliberately generous caps tuned to known free tiers. 9router
# gets a huge budget because it self-heals across upstreams; the rest are
# capped so we never trip a provider's hard "you're done for the day" wall.
# Raise these as you verify headroom on each account.
FREE_TIER_BUDGETS: dict[str, dict] = {
    # The unified fabric. We WANT to burn this — it's our own proxy.
    "9router":        {"daily_requests": 200_000, "daily_tokens": 200_000_000, "note": "Self-hosted multi-upstream proxy. Spend freely."},
    # Keyless anchors.
    "opencode-zen":   {"daily_requests": 30_000,  "daily_tokens": 15_000_000,  "note": "Keyless free tier (Novita upstream). Always available."},
    # Keyed free tiers — capped so we stay under their daily walls.
    "nvidia":         {"daily_requests": 5_000,   "daily_tokens": 5_000_000,   "note": "NVIDIA free inference."},
    "groq":           {"daily_requests": 7_000,   "daily_tokens": 4_000_000,   "note": "Groq free tier (tokens/day soft cap)."},
    "openrouter":     {"daily_requests": 10_000,  "daily_tokens": 8_000_000,   "note": "OpenRouter ':free' models."},
    "deepinfra":      {"daily_requests": 3_000,   "daily_tokens": 3_000_000,   "note": "DeepInfra free tier."},
    "huggingface":    {"daily_requests": 2_000,   "daily_tokens": 2_000_000,   "note": "HF serverless."},
    "github-models":  {"daily_requests": 5_000,   "daily_tokens": 5_000_000,   "note": "GitHub Models (free for GH users)."},
    "sambanova":      {"daily_requests": 2_000,   "daily_tokens": 2_000_000,   "note": "SambaNova free tier."},
    "together":       {"daily_requests": 2_000,   "daily_tokens": 2_000_000,   "note": "Together free credits."},
    "fireworks":      {"daily_requests": 2_000,   "daily_tokens": 2_000_000,   "note": "Fireworks free credits."},
}


# ─── Multi-key support ───────────────────────────────────────────────────────
def split_keys(env_val: Optional[str]) -> list[str]:
    """Fan a single env var into N keys.

    Accepts comma OR newline OR whitespace separated keys so you can paste a
    list of free-tier keys and multiply your quota — each key is its own
    budget slot in the router. Empty/None -> [].
    """
    if not env_val:
        return []
    out = []
    for part in re.split(r"[\s,]+", env_val.strip()):
        part = part.strip()
        if part:
            out.append(part)
    return out


# ─── 9router reset-timer parsing ─────────────────────────────────────────────
_RESET_RE = re.compile(
    r"reset\s+after\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
    re.IGNORECASE,
)


def parse_reset_seconds(text: str) -> Optional[int]:
    """Extract the cooldown window (seconds) from a 9router quota error.

    Handles: 'reset after 4m 56s', 'reset after 2m', 'reset after 120s',
    'R (reset after 4m 56s)'. Returns None if no timer is present.
    """
    if not text:
        return None
    m = _RESET_RE.search(text)
    if not m:
        return None
    h = int(m.group(1)) if m.group(1) else 0
    mi = int(m.group(2)) if m.group(2) else 0
    s = int(m.group(3)) if m.group(3) else 0
    total = h * 3600 + mi * 60 + s
    return total or None


def is_quota_error(text: str) -> bool:
    """True if the error looks like a free-tier quota / balance exhaustion."""
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in (
        "usage limit", "rate limit", "429", "402", "insufficient balance",
        "quota", "monthly limit", "daily limit", "too many requests",
    ))


# ─── Usage store (persisted) ─────────────────────────────────────────────────
def _usage_path() -> str:
    # Anchor to the project's data/ dir (two levels up from this file) so the
    # budget file is consistent no matter where the process is launched from.
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "..", "..", "data", "free_tier_usage.json")
    return os.environ.get("FT_USAGE_FILE", default)


class UsageStore:
    """Per-slot daily request/token accounting + cooldowns, persisted to JSON.

    A 'slot' is one (provider, key) pair — multiple keys for one provider
    therefore multiply the available free quota. Cooldowns are keyed by an
    arbitrary endpoint id (e.g. '9router:ocg/kimi-k2.7-code') so we can park a
    single exhausted 9router upstream without disabling the whole proxy.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path or _usage_path()
        self._data: dict = {"day": "", "slots": {}, "cooldowns": {}}
        self._load()

    # ── persistence ──
    def _load(self):
        try:
            with open(self.path, "r") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {"day": "", "slots": {}, "cooldowns": {}}
        # Roll over to a new day.
        today = time.strftime("%Y-%m-%d")
        if self._data.get("day") != today:
            self._data = {"day": today, "slots": {}, "cooldowns": {}}
            self._save()

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp, self.path)
        except OSError as e:
            logger.warning("UsageStore: could not persist %s: %s", self.path, e)

    # ── slot accounting ──
    def _slot(self, provider: str, key_index: int) -> dict:
        key = f"{provider}#{key_index}"
        slot = self._data["slots"].setdefault(key, {"requests": 0, "tokens": 0})
        return slot

    def record(self, provider: str, key_index: int = 0, requests: int = 1, tokens: int = 0):
        slot = self._slot(provider, key_index)
        slot["requests"] += requests
        slot["tokens"] += tokens
        self._save()

    def remaining(self, provider: str, key_index: int = 0) -> dict:
        budget = FREE_TIER_BUDGETS.get(provider, {"daily_requests": 1_000, "daily_tokens": 1_000_000})
        slot = self._slot(provider, key_index)
        return {
            "daily_requests": budget["daily_requests"],
            "daily_tokens": budget["daily_tokens"],
            "used_requests": slot["requests"],
            "used_tokens": slot["tokens"],
            "requests_left": max(0, budget["daily_requests"] - slot["requests"]),
            "tokens_left": max(0, budget["daily_tokens"] - slot["tokens"]),
        }

    def is_exhausted(self, provider: str, key_index: int = 0) -> bool:
        r = self.remaining(provider, key_index)
        return r["requests_left"] <= 0 or r["tokens_left"] <= 0

    # ── cooldowns (per endpoint id) ──
    def cooldown_until(self, endpoint_id: str) -> float:
        return float(self._data["cooldowns"].get(endpoint_id, 0.0))

    def set_cooldown(self, endpoint_id: str, seconds: int):
        if seconds <= 0:
            return
        self._data["cooldowns"][endpoint_id] = time.time() + seconds
        self._save()

    def is_cooled_down(self, endpoint_id: str) -> bool:
        return time.time() < self.cooldown_until(endpoint_id)

    # ── diagnostics ──
    def snapshot(self) -> dict:
        return {
            "day": self._data.get("day"),
            "slots": {
                k: {
                    **v,
                    "budget_requests": FREE_TIER_BUDGETS.get(k.split("#")[0], {}).get("daily_requests"),
                    "budget_tokens": FREE_TIER_BUDGETS.get(k.split("#")[0], {}).get("daily_tokens"),
                }
                for k, v in self._data["slots"].items()
            },
            "cooldowns": self._data.get("cooldowns", {}),
        }


# Module-level singleton so all callers share one budget view.
_store = UsageStore()


def get_store() -> UsageStore:
    return _store
