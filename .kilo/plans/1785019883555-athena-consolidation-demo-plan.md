# RealtyAI — Demo Polish + Architecture Roadmap

## Decisions (this session)

| Decision | Choice |
|----------|--------|
| Immediate priority | Demo polish — ship features on current monolith. No architectural refactoring yet |
| Vision subsystems | Deferred: voice, vision, finance, workflow engine, client portal → Roadmap Phase 2+ |
| Architecture migration | Deferred: stay FastAPI monolith + Next.js. Migrate to microservices after 5-10 paying users |
| Multi-agent framework | Deferred: Athena is the single agent for now. Multi-agent (CEO/Buyer/Seller) in Roadmap Phase 3 |

## North Star Architecture (Vision Document)

The vision document defines the 20-year target. This excerpt maps it to the current state:

| Vision Subsystem | Demo Status | Roadmap Phase |
|---|---|---|
| Authentication (RBAC, OAuth, MFA, API keys) | JWT only | Phase 2 |
| CRM (leads, clients, families, tags, timeline) | Leads + properties CRUD | Phase 2 |
| AI Memory (semantic, knowledge graph, pruning) | PostgreSQL facts + Mem0 (vector only) | Phase 2 (knowledge graph) |
| AI Agent Framework (CEO/Buyer/Seller/etc) | Athena single agent + 23 tools | Phase 3 |
| MLS Intelligence (comps, price prediction, alerts) | Scraper + market_snapshot | Phase 2 |
| Marketing Platform (email, SMS, social, SEO) | Campaign stub | Phase 3 |
| Voice System | Not started | Phase 4 |
| Vision System | Not started | Phase 4 |
| Document Platform (OCR, signatures, templates) | Contract summary + deadline extraction | Phase 2 |
| Workflow Engine (automation builder) | Not started | Phase 4 |
| Calendar (availability, route planning) | Showing scheduling tool | Phase 2 |
| Finance (commissions, forecasting) | Not started | Phase 4 |
| Analytics (KPIs, conversion, predictive) | Basic stats dashboard | Phase 2 |
| Client Portal (buyer/seller dashboards) | Not started | Phase 3 |
| Admin Portal (monitoring, billing, feature flags) | Not started | Phase 4 |
| Database (relational, vector, graph, cache) | PostgreSQL + Qdrant vectors only | Phase 2 (graph) |
| Event System (event-driven architecture) | None | Phase 3 |

## Current State: What's Working

| Feature | Status |
|---------|--------|
| FastAPI monolith backend on VPS (185.80.130.197) | ✅ |
| Next.js 15 frontend on Vercel | ✅ |
| JWT auth (register/login) | ✅ |
| Athena chat with 23 tools | ✅ |
| LangChain tool-calling agent (DeepSeek v4 Flash) | ✅ |
| Scraper: Zillow via Jina Reader | ✅ |
| Scrape → DB insert pipeline | ✅ |
| Property detail page `/dashboard/listings/[id]` | ✅ |
| Property import button (Scrape New Listings) | ✅ |
| Lead auto-scoring on creation | ✅ |
| Leads kanban + scoring | ✅ |
| Listings grid + search | ✅ |
| Calendar page (from showings table) | ✅ |
| Sidebar: core 7 + More menu | ✅ |
| Capabilities page (23 tools grouped) | ✅ |
| CoverAge sidebar: core 7 + More menu | ✅ |
| Briefing endpoint `GET /briefing` | ✅ |
| Dashboard recommendations `GET /api/v1/dashboard/recommendations` | ✅ |
| Document: summarize_contract + extract_deadlines tools | ✅ |
| Multi-tenant: agent_id scoping on leads, listings, conversations | ✅ |

## Current State: What's Broken

| Issue | File | Fix |
|-------|------|-----|
| Mem0 "Not Available" on VPS | `mem0_adapter.py`, `Dockerfile` | fastembed not in Docker build. Install via deps + fix embedder fallback |
| Image thumbnails not in chat responses | `zillow.py`, frontend `renderMarkdown` | Scan window fixed (i+12→i+25) — verify deployed. Jina returns `.webp` images |
| Listing card images empty | `api.ts:normalizeProperty` | DB stores flat array now. Frontend handles dict→array. Verify end-to-end |
| Daily briefing hardcodes "Sarah" | `packages/ai/briefing.py` | Already fixed in code — verify deployed |
| Frontend hydration errors on custom domain | `page.tsx` | Next.js client/server mismatch — verify on realty.indicationsmedia.com |
| Empty user dashboard shows "no recent activity" | `main.py:recommendations` | Already added "get started" rec — verify deployed |

## Phase 1: Fix Critical Demo Blockers

### 1.1 Fix Mem0 on VPS (must do — blocks memory features)
- **Root cause**: `fastembed` and `mem0ai` packages not properly installed in Docker build. The embedder fallback hits `openai` provider with no API key, times out after 60s, returns None.
- **Fix**: 
  - Added `fastembed>=0.8.0` to hermes pyproject.toml deps → committed in `8f54b65`
  - Dockerfile line 33 changed from `sentence-transformers` to `fastembed`
  - `mem0_adapter.py` embedder config now includes `DEEPSEEK_API_KEY` as fallback for openai provider
  - Need to verify VPS build includes fastembed. Check build logs
  - Fallback: if fastembed fails, set `MEM0_EMBEDDER_PROVIDER=openai` with `OPENAI_API_KEY` pointing to DeepSeek's API
- **Validate**: `curl http://185.80.130.197:8000/api/v1/athena/memories/count` → `{"count": ..., "enabled": true}`

### 1.2 Verify Image Pipeline Works End-to-End
- Scan window fix `efe3c65` deployed. Jina images at `photos.zillowstatic.com` with `.webp`
- Verify deploy: `curl http://185.80.130.197:8000/health`
- Test: chat "scrape 3 properties in Edmonton" → verify `![alt](img_url)` lines in response
- Frontend `renderMarkdown` at `page.tsx:57-59` handles `![alt](url)` → `<img>` tag
- Pipeline stores flat `["url1","url2","url3"]` array in `images` JSONB column
- `normalizeProperty` handles flat array, dict wrapper, and string JSON

### 1.3 Verify Fresh User Onboarding
- Register new user → dashboard shows empty with "get started" recommendation
- Scrape 3 properties → dashboard shows 3 listings with thumbnails
- No leaked data from other users
- Verify agent_id scoping on leads, listings, conversations

### 1.4 Fix Daily Briefing Name (if not deployed)
- `GET /briefing` should greet by `current_user.name`, not hardcoded "Sarah"
- Code fix already in `main.py` — verify deployed

### 1.5 Verify Lead-to-Showing Flow
- Scrape properties → score leads → click lead → follow-up recommendations
- Schedule showing from property detail page → appears on calendar
- Calendar page shows color-coded events

## Phase 2: Feature Round-out (post-blockers)

### 2.1 Document Upload + Analysis Flow
- Frontend: upload PDF on documents page
- Click "Analyze" → Athena receives context about the document
- Chat: "summarize this contract", "extract deadlines"
- API `POST /api/v1/documents/{id}/ask` already exists — wire frontend

### 2.2 Email/SMS Notification Stubs
- When lead score changes, create notification record
- When showing is scheduled, notify agent
- Notification center component on dashboard
- No actual email/SMS sending — just in-app notifications for demo

### 2.3 Analytics Dashboard Polish
- Current analytics page shows basic stats from dashboard summary
- Add: lead conversion funnel (new → qualified → contacted → closed)
- Add: listing status breakdown (active vs pending vs sold)
- Add: agent activity timeline (last 30 days)

### 2.4 Frontend UX Polish
- Loading skeletons on all data-fetching pages
- Error states instead of blank pages
- Toast notifications for successful actions (scrape complete, lead scored, showing scheduled)
- Mobile-responsive chat input and sidebar
- Fix hydration errors on custom domain

## Phase 3 (Roadmap): Multi-Agent Framework

After demo is polished and real users are onboard:

### 3.1 Agent Architecture
- Athena becomes the CEO/Orchestrator agent
- Specialized sub-agents:
  - **Lead Agent**: qualifies leads, scores pipeline, recommends follow-ups
  - **Listing Agent**: generates MLS descriptions, compares properties
  - **Market Agent**: market snapshots, trends, neighborhood analysis
  - **Document Agent**: contract analysis, deadline extraction, RAG
  - **Scheduling Agent**: showing management, calendar integration
  - **Research Agent**: web browsing, market data, competitor analysis
- Agents communicate via message passing (not shared state)
- Each agent has its own memory, tools, and system prompt
- Athena delegates tasks and synthesizes responses

### 3.2 Knowledge Graph
- Add Neo4j or PostgreSQL graph extensions
- Entities: Person, Property, Brokerage, Neighborhood, Document, Showing, Lead
- Relationships: OWNS, LISTED_BY, INTERESTED_IN, SCHEDULED, REFERRED
- Query: "show me all leads interested in properties in Windermere under $500k" → graph traversal + vector search

### 3.3 Event Bus
- Introduce Redis pub/sub or RabbitMQ
- Events: LeadCreated, PropertyScraped, ShowingScheduled, LeadScored, DocumentUploaded
- Subscribers: notification service (email/SMS), analytics aggregator, memory consolidator
- Benefits: loose coupling between features, easier to add new services later

## Phase 4 (Roadmap): Enterprise

### 4.1 Multi-Brokerage / Teams
- Organization hierarchy: Brokerage → Team → Agent
- Team lead can view all team members' leads and listings
- Brokerage admin can manage all teams
- Organization-level analytics and reporting

### 4.2 White Label
- Custom domain per brokerage
- Custom branding (logo, colors, email templates)
- Configurable feature flags per organization

### 4.3 API Ecosystem
- Public REST API for third-party integrations
- Webhook subscriptions for events
- Plugin marketplace for custom tools
- SDK for custom agent tools

## Files Likely to Change (Phase 1)

| File | Action |
|------|--------|
| `packages/hermes/src/hermes/mem0_adapter.py` | Verify embedder fallback works without API key |
| `apps/api/Dockerfile` | Verify fastembed pip install succeeds |
| `packages/hermes/src/hermes/scraper/zillow.py` | Verify scan window + image extraction deployed |
| `apps/web/src/app/dashboard/athena/page.tsx` | Verify renderMarkdown handles images |
| `apps/web/src/lib/api.ts` | Verify normalizeProperty handles flat array |
| `apps/api/src/main.py` | Verify briefing name fix deployed |
| `apps/web/src/app/dashboard/listings/[id]/page.tsx` | Created — verify renders correctly |
| `apps/web/src/app/dashboard/listings/page.tsx` | Updated with scrape button — verify |

## Validation Plan

After each fix:
1. `python3 -c "import ast; ast.parse(open('path').read()); print('OK')"` — all Python files parse
2. `curl http://185.80.130.197:8000/health` — backend healthy
3. `curl https://realty-ai-ten.vercel.app/` — frontend loads
4. Browser: hard refresh (Ctrl+Shift+R) → login → test the fixed flow

End-to-end demo test:
1. New user registers → empty dashboard
2. Chat: "scrape 5 properties in Edmonton and import them"
3. Images rendered in chat
4. Listing cards show thumbnails → click → detail page with gallery
5. Chat: "score my leads" → scores appear
6. Leads kanban shows scored leads
7. Property detail → "Generate Description" → AI description
8. Schedule showing → appears on calendar
9. Dashboard shows recommendations
10. Check `/api/v1/athena/memories` → Mem0 enabled
