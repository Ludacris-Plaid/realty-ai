# Guerrilla Free-Tier System — "Keep Us Coding for $0"

> We are poor and building toward bigger projects. Every dollar saved on LLM
> inference is a dollar toward the next build. This system exists to make sure
> **no Athena/coding call ever costs money** by maxing out our own 9router
> proxy and falling across a pool of free providers with quota-aware routing.

## The one asset that matters: 9router

`9router` is a self-hosted multi-upstream proxy (Cloudflare tunnel + local
proxy on `http://localhost:20128/v1`). It aggregates **~80 free/cheap models**
across providers and exposes them as OpenAI-compatible endpoints:

| Prefix   | Upstream pool                                  | Notes |
|----------|------------------------------------------------|-------|
| `ds/`    | DeepSeek (chat, reasoner, v4 pro/flash)        | Balance-limited, resets on timer |
| `nvidia/`| NVIDIA (kimi-k2.6, glm-5.2, minimax, nemotron) | Free inference |
| `openai/`| OpenAI-proxied (gpt-5.4-nano, gpt-4o, o3…)     | Via 9router upstreams |
| `ocg/`   | opencode-go (kimi-code, qwen, deepseek, glm)   | Monthly usage caps |
| `cf/`    | Cloudflare Workers AI (llama, kimi, glm)       | Free tier |

`combo_test` round-robins across **all** of them and self-heals on quota
errors. But each upstream has its own limit that resets on a timer
(`reset after 4m 56s`). Blindly hammering `combo_test` wastes slots on dead
upstreams.

## How the guerrilla router works (`packages/ai/free_llm.py`)

`ResilientLLM` is a `ChatOpenAI`-compatible wrapper that:

1. **Fans providers out into concrete endpoints.** Each provider × base ×
   key × model becomes one endpoint. For 9router that's
   `9 upstreams × {local keyless + tunnel keyed}` = 18 endpoints, plus
   `opencode-zen`, `groq`, `openrouter`, … Only providers with a key (or that
   are keyless) join.
2. **MAXES OUT 9router first.** 9router is priority #1. We rotate across its
   *specific* upstreams (not just `combo_test`) so load is spread and a single
   exhausted upstream doesn't sink the whole call.
3. **Parses 9router's own reset timers.** When an upstream returns
   `reset after 4m 56s`, we cool *just that endpoint* for exactly that window
   (capped at 6h) instead of guessing. The rest of 9router keeps serving.
4. **Falls back only when 9router is cooling.** Next healthy endpoint wins —
   the broader free pool (Groq, OpenRouter, NVIDIA, …) or the keyless
   `opencode-zen` anchor.
5. **Enforces daily budgets** per (provider, key) slot so we never trip a
   provider's hard "you're done for the day" wall. Usage + cooldowns persist
   to `data/free_tier_usage.json` and survive restarts.

## Multiply free quota with MULTIPLE KEYS

Every keyed provider accepts **multiple keys** in one env var — comma, space,
or newline separated. Each key becomes its own budget slot, so one config
fans out into N independent quotas:

```bash
# .env — three Groq accounts = 3× the free quota
GROQ_API_KEY=gsk-aaa,gsk-bbb,gsk-ccc
# three OpenRouter accounts
OPENROUTER_API_KEY=sk-or-1,sk-or-2,sk-or-3
```

Legitimate ways to multiply free quota (no abuse, no fake accounts):
- Separate free-tier accounts per real email (personal, work, project inboxes).
- 9router already aggregates many upstreams under one roof — that's the
  biggest multiplier we have.
- GitHub Models is free for any GitHub user with a token.
- Run the local 9router proxy on multiple machines (each is keyless).

## Wiring

- `llm_config.get_model()` returns the guerrilla `ResilientLLM` as primary.
  Set `GUERRILLA_LLM=0` to fall back to the legacy tiered chain.
- Athena's `agent.py` uses `get_model()`, so the whole agent now routes free.
- `build_resilient_llm()` / `build_guerrilla_llm()` are the factories.

## Live status

```bash
python packages/ai/free_tier_status.py          # human-readable burn + health
python packages/ai/free_tier_status.py --json    # raw JSON for dashboards
```

## Add a provider

Append a dict to `FREE_PROVIDERS` in `free_llm.py` (name, base, key_env, model,
keyless/key_optional). Add its daily budget to `FREE_TIER_BUDGETS` in
`free_tier.py`. Done — it auto-joins the rotation.

## Add a 9router upstream

Append the model id to `NINEROUTER_UPSTREAMS` in `free_llm.py` (must be a model
returned by `http://localhost:20128/v1/models`). It becomes its own endpoint
with its own quota-aware cooldown.

## Boundary (stay legit)

This system maximizes *legitimate* free tiers and our own infrastructure. It
does **not** automate creation of fake accounts to farm quota — that risks
bans and breaks the trust of the free providers we depend on. Multiply quota
through real separate accounts and 9router's aggregation, not deception.
