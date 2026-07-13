# ATHENA PLAN — Build the SaaS Empire

> **Core thesis**: Athena is not a feature. Athena *is* the product. Every screen, every button, every workflow exists to serve the relationship between the agent and their digital secretary. The SaaS is the container; Athena is the reason people pay.

---

## I. Vision Statement

**RealtyAI + Athena** becomes the operating system for real estate professionals in North America. A single login that runs the entire business — leads, listings, documents, marketing, compliance — through a natural conversation with a digital secretary who knows you, learns your style, and proactively runs your business.

### North Star Metric
**Monthly active conversations per agent** — not logins, not page views. If Athena is the interface, conversation frequency is the only metric that matters.

---

## II. Product Architecture

```
                    ┌─────────────────────┐
                    │   ATHENA INTERFACE   │
                    │  (The only UI that   │
                    │   matters long-term) │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │  MEMORY    │ │  PROACTIVE │ │  TOOLS     │
     │  (Mem0)    │ │  ENGINE    │ │ (16 tools) │
     └────────────┘ └────────────┘ └────────────┘
              │              │              │
              ▼              ▼              ▼
     ┌─────────────────────────────────────────┐
     │            DATA PLATFORM                │
     │  PostgreSQL · Redis · pgvector · S3     │
     └─────────────────────────────────────────┘
```

### The Three Pillars

1. **Memory Layer (Mem0)** — Athena remembers everything. Facts, preferences, past conversations, client interactions, deal history. No manual memory management.

2. **Proactive Engine** — Athena doesn't wait to be asked. She surfaces lead alerts, deadline reminders, market changes, daily briefings — on schedule and by context.

3. **Tool Layer** — Athena controls the entire platform. She clicks every button, reads every report, sends every email. The UI exists only as a fallback.

---

## III. Phased Build Plan

### Phase 1: Foundation ✅ *(Complete)*
- [x] Rename Hermes → Athena (code, routes, branding)
- [x] Amber/gold brand identity across all surfaces
- [x] Persistent conversation history (SQLite → survives page reload)
- [x] Floating Athena assistant on every dashboard page
- [x] Auto-expanding chat input, markdown rendering, copy-to-clipboard
- [x] System overview, memory view, stat cards
- [x] Basic tool calling (16 tools: leads, listings, documents, etc.)
- [x] 4-tier LLM fallback chain (OpenCode Zen → 9router → Featherless → NVIDIA)
- [x] Railway backend + Vercel frontend deployment pipeline

**Issues carried forward:**
- Tool calling emits raw XML on hy3-free model (no structured function-calling)
- No authentication
- Activity feed and approvals are in-memory (lost on restart)
- Dual DB access layers (SQLite for Athena, PostgreSQL for everything else)
- All specialist agents return mock data

### Phase 2: Memory & Identity 🎯 *(In Progress)*

**Goal**: Athena remembers who you are, what you did, and what matters — across sessions, across devices, across platforms (web, Telegram, Slack).

| Step | Task | Status | Details |
|------|------|--------|---------|
| 2.1 | Multi-channel architecture | ✅ Done | Created `/packages/bots` with Telegram and Slack adapters. Webhook endpoints at `/api/v1/athena/telegram/webhook` and `/api/v1/athena/slack/events`. Messages from all channels route through the same Athena agent with shared conversation history. |
| 2.2 | Telegram bot adapter | ✅ Done | `bots.telegram` module — handles webhook updates, sends typing indicator, routes to Athena, formats responses. `set_webhook()` to register URL. Enable by setting `TELEGRAM_BOT_TOKEN` env var. |
| 2.3 | Slack bot adapter | ✅ Done | `bots.slack` module — handles Events API (messages), verifies Slack signing secret, handles URL verification challenge, routes to Athena. Enable by setting `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET` env vars. |
| 2.4 | Bot status dashboard | ✅ Done | `GET /api/v1/athena/bots/status` — shows which integrations are configured. |
| 2.5 | Integrate Mem0 | 🟡 Partial | Adapter exists (`hermes/mem0_adapter.py`) with Qdrant vector store, automatic entity extraction, semantic search, cross-session context retrieval. Wired into `agent.py` post-chat learning loop + memory injection. Needs production verification: pip package install, init timeout on Railway, Qdrant disk usage. |
| 2.6 | User profiles | ☐ Pending | Multi-agent firm support — each agent has their own Athena profile, memory, and preferences. Requires auth layer. |
| 2.7 | Conversation search | 🟡 Partial | FTS5 full-text search on past conversations works (SQLite). Semantic cross-session search via Mem0 works. No unified search UI combining both. |
| 2.8 | Cross-session context | ☐ Pending | Mem0 `get_relevant_context()` wired into system prompt, but greeting is still generic ("Good morning") — no personalized "Welcome back, Mike's offer was accepted" yet. |
| 2.9 | Memory dashboard | ✅ Done | Frontend Memory view tab shows profile + skills. CRUD API endpoints at `/api/v1/athena/memories` (list, search, delete, count). Edit/delete facts via API. |

**Device continuity**: All conversations are stored server-side. You can start on Telegram, continue on the web dashboard, then follow up via Slack — the same Athena, the same memory, the same conversation history. **scrcpy is not needed** for this use case — scrcpy is a screen mirroring tool (displays Android screen on desktop), not a session migration tool. Server-side state with multi-channel support is the correct architecture for device continuity.

### Phase 3: Proactive Engine 🚨 *(3 weeks)*

**Goal**: Athena initiates — she doesn't wait for commands.

| Step | Task | Details |
|------|------|---------|
| 3.1 | Daily briefing | Auto-generated morning brief: hot leads, expiring listings, deadlines, market changes. Pushed to dashboard + optional email. |
| 3.2 | Lead alerts | Real-time notifications when high-scoring leads enter the system, go cold, or change status. "Mike Chen (score 92) just viewed the Windermere listing for the 3rd time." |
| 3.3 | Deadline tracker | Ingentive deadlines, closing dates, inspection windows, license renewals. Proactive reminders with configurable lead time. |
| 3.4 | Market monitoring | Price changes in tracked neighborhoods, new listings matching saved searches, days-on-market alerts for stale listings. |
| 3.5 | Smart nudges | "You haven't followed up with Emily Davis in 5 days. She was pre-approved for 850k. Want me to draft an email?" |

**Deliverable**: Athena is the first thing the agent sees in the morning and the last thing at night.

### Phase 4: Legal RAG ⚖️ *(3 weeks)*

**Goal**: Athena understands Canadian and US real estate law end-to-end.

| Step | Task | Details |
|------|------|---------|
| 4.1 | Corpus ingestion | Ingest OREA forms, RESPA guidelines, TREC rules, provincial real estate acts, standard contract clauses into vector store. |
| 4.2 | Legal Q&A | "What's the cooling-off period in Ontario?" → Athena cites the exact regulation and clause. |
| 4.3 | Contract analysis | Upload a purchase agreement → Athena extracts key terms, deadlines, risks, non-standard clauses. "This contract has an unusual financing contingency on line 47." |
| 4.4 | Compliance checks | "Does this marketing email comply with CAN-SPAM?" / "Is this referral fee arrangement legal in Alberta?" |
| 4.5 | Jurisdiction detection | Auto-detects province/state from listing/lead address and applies correct legal framework. |
| 4.6 | Disclaimer system | Always includes appropriate disclaimers ("I'm AI, not a lawyer") when discussing legal matters. |

**Deliverable**: Agents ask Athena legal questions instead of calling their broker or lawyer for routine matters.

### Phase 5: Voice & Mobile 🎙️ *(3 weeks)*

**Goal**: Athena in your ear, in your pocket, hands-free.

| Step | Task | Details |
|------|------|---------|
| 5.1 | Deepgram STT | Real-time speech-to-text for voice input. Low latency, high accuracy for real estate terminology. |
| 5.2 | ElevenLabs TTS | Premium text-to-speech with warm, professional voice. Personality-matched to Athena brand. |
| 5.3 | Voice conversation | Full duplex conversation — speak to Athena, she speaks back. "Athena, what's my first showing tomorrow?" |
| 5.4 | Mobile PWA | Progressive web app with voice-first interface. Athena is a home screen icon, not a URL. |
| 5.5 | Hands-free mode | Driving mode — voice-only, no taps. "Call Mike Chen" / "Text Emily the address" / "What's my pipeline worth?" |
| 5.6 | Voice wake word | "Hey Athena" hands-free activation (optional, privacy-first). |

**Deliverable**: Agents interact with Athena more than any human colleague because she's always available.

### Phase 5.5: CRM Integrations 🔗 *(3 weeks, parallel with Voice)*

**Goal**: Athena syncs bidirectionally with the CRMs agents already live in.

| Step | Task | Details |
|------|------|---------|
| 5.5.1 | Adapter layer | Abstract `CRMAdapter` base class — `push_lead()`, `pull_leads()`, `push_note()`, `sync_status()`. Each CRM is a plugin. |
| 5.5.2 | Field mapping engine | Flexible JSON field map per CRM. "deal" → "lead", "opportunity_stage" → "status". UI to customize per brokerage. |
| 5.5.3 | Conflict resolution | Last-write-wins by default, configurable per field. Athena as source-of-truth for AI score; CRM as source-of-truth for contact details. |
| 5.5.4 | Follow Up Boss | Highest-priority: dominant in residential RE. Two-way lead + note sync via FUB REST API. |
| 5.5.5 | HubSpot | Contacts + deals sync. Webhook listener for real-time CRM → Athena updates. |
| 5.5.6 | Salesforce | Enterprise tier only. Bulk API for initial import, Streaming API for real-time. |
| 5.5.7 | kvCORE / Lofty | Common in team/brokerage setups. Lead import + status pushback. |
| 5.5.8 | Webhook inbound | Generic inbound webhook endpoint — any CRM can POST lead events to Athena. |
| 5.5.9 | Sync dashboard | UI showing last sync time, conflict log, field mapping editor, enable/disable per integration. |

**Key design decisions (captured from product review):**
- Two-way sync is the baseline — not just pull-in, push status/notes back so nothing drifts
- Field mapping is per-brokerage configurable, not hardcoded
- Conflict resolution policy decided at schema design time: AI score owned by Athena, contact data owned by CRM, timestamps break ties

**Deliverable**: An agent's existing CRM stays in sync automatically. Athena becomes the AI brain on top of whatever CRM they already paid for.

### Phase 6: Continuous Learning 🧠 *(Ongoing)*

**Goal**: Athena gets better every day without engineering intervention.

| Step | Task | Details |
|------|------|---------|
| 6.1 | Feedback loop | Thumbs up/down on every response. Train on high-rated exchanges. |
| 6.2 | Sleep-time compute | Overnight processing: consolidate memory, generate briefings, analyze patterns, surface insights. |
| 6.3 | Skill emergence | Athena detects repeated workflows and auto-creates skills. "You've run 'compare these 3 listings' 5 times — want me to make it a one-click skill?" |
| 6.4 | Personalization model | Fine-tune response style per agent. Some want formal, some want casual. Athena adapts. |
| 6.5 | Anomaly detection | Athena flags unusual patterns: "You usually close 40% of leads from Zillow, but this month it's 12%. Want me to investigate?" |

**Deliverable**: Athena improves measurably each week with zero developer time.

---

## IV. SaaS Business Model

### Tier Structure

| Tier | Price | Key Limit |
|------|-------|-----------|
| **Starter** | $29/mo | 1 agent, 500 conversations/mo, basic memory |
| **Pro** | $79/mo | 3 agents, unlimited conversations, full memory, proactive engine |
| **Team** | $199/mo | 10 agents, all features, shared memory, manager dashboard |
| **Enterprise** | Custom | Unlimited agents, white-label, SLA, on-premise option |

### Differentiation

**Why win against:**
- **Follow-up Boss / Lofty / kvCORE**: They're CRMs with chat. Athena is an *agent* with a CRM. The relationship model beats the database model.
- **ChatGPT / Claude**: Generic models don't know real estate. Athena knows OREA forms, RESPA, Edmonton vs Toronto vs Austin, and your business personally.
- **Bard / Copilot**: Not built for real estate workflows. Athena has 16+ real estate tools built in.

### Revenue model
- **Direct**: Monthly/annual subscriptions per seat
- **Transaction**: Premium tier for teams ($199 → high margin)
- **Services**: Compliance audits, custom integrations, training
- **Marketplace** (future): Third-party skill marketplace (like Slack Apps but for real estate AI)

---

## V. Technical Debt & Infrastructure

### Must-fix before Enterprise launch

| Issue | Priority | Fix |
|-------|----------|-----|
| No authentication | 🔴 Critical | Auth0 or Clerk integration. Every endpoint needs a user. |
| In-memory activity/approval | 🔴 Critical | Move to PostgreSQL tables. |
| Dual DB (SQLite + PostgreSQL) | 🟡 High | Move Athena memory to PostgreSQL. One database to rule them all. |
| XML tool calling | 🟡 High | Switch model or add XML→JSON post-processor for hy3-free. |
| Mock data in specialist agents | 🟡 High | Wire agents to real database queries. |
| No file upload UI for documents | 🟢 Medium | Now handled (hidden input), needs drag-and-drop UX. |
| Hardcoded UUIDs in v1 endpoints | 🟢 Medium | Pull from auth context. |
| Calendar is hardcoded | 🟢 Medium | Connect to Google Calendar API. |
| Settings don't save | 🟢 Medium | Wire to PostgreSQL profile table. |
| No error boundaries | 🟢 Medium | Add React error boundaries per page. |
| Hardcoded "Sarah Chen" everywhere | 🟢 Low | Pull from user profile. |

---

## VI. Success Metrics

### Leading indicators (weekly)
- **Conversations per agent**: Target > 50/week for active users
- **Memory growth**: New facts/persona learned per conversation
- **Tool call success rate**: > 90% (currently broken with XML issue)
- **Proactive engagement rate**: % of proactive alerts that lead to agent action

### Lagging indicators (monthly)
- **Retention**: Day-7, Day-30, Day-90
- **Time-to-value**: Minutes from signup to first "aha" moment
- **NPS**: Measured quarterly
- **Revenue**: MRR, ARPU, churn

---

## VII. Immediate Next Steps (This Week)

1. Fix tool-calling XML issue (switch model or add parser)
2. Add authentication (Clerk or Auth0)
3. Start Mem0 integration (Phase 2.1)
4. Move in-memory stores to PostgreSQL
5. Wire specialist agents to real data

---

## VIII. The Long Game (6-12 months)

- **Multi-brokerage mode**: Brokerages manage their agents, see team-wide analytics, enforce compliance
- **Consumer-facing portal**: Clients get their own Athena-lite view — "Where's my offer?" / "Upload my documents"
- **Transaction management**: End-to-end deal desk with digital signatures, milestone tracking, commission splits
- **Predictive analytics**: "This lead has a 78% chance of converting in the next 14 days. Here's exactly what to say."
- **Marketplace**: Third-party skill developers build on Athena's tool layer (inspection scheduling, mortgage pre-approval, title search)

---

> **The ultimate goal**: A real estate agent's entire day — from morning briefing to last deal signed — runs through Athena. Not through a dashboard. Through a **relationship**.
