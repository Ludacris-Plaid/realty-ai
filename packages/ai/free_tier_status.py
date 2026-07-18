#!/usr/bin/env python3
"""
RealtyAI — Guerrilla Free-Tier Status CLI.

Shows live free-tier burn across every provider/key slot and which endpoint
actually served the last call. Run from anywhere:

    python -m free_tier_status
    python packages/ai/free_tier_status.py

Env:
    FT_USAGE_FILE   override the persisted usage JSON path
"""
import os
import sys
import json
import argparse
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _load():
    # Make the package importable whether run as module or script.
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        from free_llm import ResilientLLM, _expand_endpoints
        from free_tier import get_store, FREE_TIER_BUDGETS
        return ResilientLLM(), _expand_endpoints(), get_store(), FREE_TIER_BUDGETS
    except Exception as e:  # pragma: no cover
        logger.error("Could not load guerrilla pool: %s", e)
        raise SystemExit(1)


def _bar(pct: float, width: int = 24) -> str:
    pct = max(0.0, min(1.0, pct))
    filled = int(pct * width)
    return "█" * filled + "·" * (width - filled)


def main():
    ap = argparse.ArgumentParser(description="Guerrilla free-tier status")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    llm, endpoints, store, budgets = _load()
    st = llm.status()

    if args.json:
        print(json.dumps(st, indent=2, default=str))
        return

    print("═" * 64)
    print("  REALTYAI — GUERRILLA FREE-TIER STATUS")
    print("═" * 64)
    print(f"  Endpoints live : {st['endpoint_count']}")
    print(f"  Last served by : {st['last_provider'] or '(none yet)'}")
    print()

    # Per-slot budget burn.
    print("  DAILY BUDGET BURN (per provider/key slot)")
    print("  " + "-" * 60)
    snap = store.snapshot()
    for slot_key, slot in sorted(snap.get("slots", {}).items()):
        prov = slot_key.split("#")[0]
        bud = budgets.get(prov, {})
        breq = bud.get("daily_requests", 0) or 1
        btok = bud.get("daily_tokens", 0) or 1
        rpct = slot["requests"] / breq
        tpct = slot["tokens"] / btok
        print(f"  {slot_key:<22} req {slot['requests']:>6}/{breq:<6} {_bar(rpct)} {rpct*100:5.1f}%")
        print(f"  {'':<22} tok {slot['tokens']:>6}/{btok:<6} {_bar(tpct)} {tpct*100:5.1f}%")
    print()

    # Endpoint health.
    print("  ENDPOINT HEALTH")
    print("  " + "-" * 60)
    for ep in st["endpoints"]:
        flag = "COOL" if ep["cooled_down"] else "up "
        print(f"  [{flag}] {ep['id']:<34} req_left={ep['budget']['requests_left']}")
    print()
    print("  Strategy: 9router is maxed first (specific upstreams, quota-aware")
    print("  cooldowns), then the broader free pool; opencode-zen is the anchor.")
    print("═" * 64)


if __name__ == "__main__":
    main()
