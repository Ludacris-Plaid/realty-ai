# RealtyAI — Athena Consolidation + Demo Readiness Plan

## Decisions Made

| Decision | Choice |
|----------|--------|
| Agent system | Merge everything into Athena. Delete `packages/ai/agents/` + `packages/ai/crews/`. Keep `packages/ai/` utility modules (briefing, activity, approval, prompts, router, llm_config) |
| CrewAI | Delete all 3 commented-out crew stubs + remove `get_crew_info`/`run_crew` tools |
| Specialist capabilities | Port 4 unique capabilities to Athena: lead scoring algorithm, follow-up recommendations, MLS price analysis, market trend report |
| Lead scoring | Auto-score on creation. Algorithm: pre-approval +20, timeline urgency +15, budget tier +10, source quality +5-10 |
| AI Agents page | Transform to "Capabilities" page listing Athena's 25 tools grouped by category |
| Sidebar | Core 7: Athena, Dashboard, Leads, Listings, Calendar, Documents, Settings. Analytics, Marketing, Memory, Capabilities behind "More" menu |
| Property detail | Create `/dashboard/listings/[id]` full page: image gallery, all fields, AI description, schedule showing |
| Demo scope | All four: scrape→listings→import, lead pipeline with scoring, property detail + MLS, daily briefing + proactive AI |

---

## Phase 1: Code Cleanup — Remove CrewAI + Specialist Agents

### 1.1 Delete directories
```
rm -rf packages/ai/crews/
rm -rf packages/ai/agents/
```

### 1.2 Strip CrewAI from Athena tools (`packages/hermes/src/hermes/tools.py`)
- Remove `get_crew_info` and `run_crew` from `TOOL_DEFINITIONS` (entries at lines 102-106)
- Remove `_get_crew_info` function (lines 796-826)
- Remove `_run_crew` function (lines 935-975)
- Remove `_run_specialist_crew` function (lines 858-932)
- Remove `_format_crew_output` helper (lines 848-855)
- Remove `_crew_arg` helper (lines 833-845)
- Remove `run_crew` tool dispatch in `execute_tool` (lines 233-234)
- Remove `get_crew_info` tool dispatch in `execute_tool` (lines 231-232)
- Remove crew-related imports from `_run_specialist_crew` (lines 865-921)

### 1.3 Update Athena system prompt (`packages/hermes/src/hermes/agent.py`)
- Remove any mention of `get_crew_info()` and `run_crew()`
- Update tool listing if system prompt references crew tools

### 1.4 Clean up API endpoints (`apps/api/src/main.py`)
- Remove `post /ai` endpoint (LangGraph supervisor, dead without agents)
- Remove `get /supervisor/route` endpoint
- Remove `get /supervisor/agents` endpoint
- Remove imports for `agent.ask`, `supervisor.route`, `supervisor.classify_intent`, `AGENT_REGISTRY`
- Update `GET /api/v1/athena/system-overview` to not reference `AGENT_REGISTRY`

### 1.5 Clean up API router (`apps/api/src/api/router.py`) if any agent routes
- Check for `/api/v1/agent/*` routes and remove

### 1.6 Verify nothing else imports from deleted packages
- grep for `from agents.` and `from crews.` and `from .agents.` across the codebase

---

## Phase 2: Port Specialist Capabilities to Athena

### 2.1 New tool: `score_lead` (lead_agent.py algorithm)
Port scoring from `packages/ai/agents/lead_agent.py`:
- Pre-approval: +20
- Timeline urgency: "immediate" +15, "1-3 months" +10, "3-6 months" +5
- Budget tier: ≥800k +10, ≥500k +7, ≥300k +5
- Lead source: referral +10, open_house +5, website +3
- Status bonus: already contacted +10, appointment set +15
- Cap at 100

Add to `TOOL_DEFINITIONS` and `execute_tool` in tools.py. Tool calls the existing `PATCH /api/v1/leads/{id}/score` logic but embedded in Athena.

### 2.2 New tool: `recommend_follow_up`
For a given lead, analyze their stage and suggest next action:
- Hot lead (score ≥80): "Call today — ask about their timeline"
- Warm lead (score 50-79): "Send listing alert matching their criteria"
- Cold lead (score <50): "Nurture campaign — send monthly market report"
- dormant leads: "Re-engagement email with new listings"

Add to `TOOL_DEFINITIONS` and implement in tools.py.

### 2.3 New tool: `property_price_analysis`
Given a property ID or address, query DB for comparable properties:
- Same city, ±20% sqft, ±20% price within last 90 days
- Return median price/sqft, count of comparables, range
- Flag: above market, at market, below market

Add to `TOOL_DEFINITIONS` and implement in tools.py.

### 2.4 New tool: `market_trend_report`
Broader market analysis than `market_snapshot`:
- Query properties grouped by city, status
- Active vs pending vs sold counts
- Median days on market (if data exists)
- YoY price change (if data exists)
- Top neighborhoods by listing count

Add to `TOOL_DEFINITIONS` and implement in tools.py. Uses existing `market_snapshot` as base.

### 2.5 Update tool count
After removals (crew_info, run_crew = 2 removed) and additions (score_lead, recommend_follow_up, property_price_analysis, market_trend_report = 4 added): 23 tools total.

---

## Phase 3: Demo Feature Completeness

### 3.1 Fix scraper image pipeline (critical — already in progress)
- **Scan window**: Already pushed in `efe3c65` (i+12→i+25). Verify deploy completed.
- **Image extraction**: `_extract_img` matches `photos.zillowstatic.com` URLs. Verified working.
- **Pipeline images**: `_insert_properties` stores flat `["url1","url2","url3"]` JSON array. Verified.
- **Frontend normalizeProperty**: handles flat array, dict wrapper, and string. Verified.
- **renderMarkdown**: handles `![alt](url)` → `<img>` tag. Verified.

Verify end-to-end: scrape → images in chat response → imported to DB → listing cards show thumbnails.

### 3.2 Auto-score leads on creation
- **File**: `apps/api/src/api/v1/leads.py` — `create_lead` function
- After INSERT, call scoring logic and UPDATE the row with ai_score and ai_score_reason
- Use same algorithm as the new `score_lead` tool

### 3.3 Add "Import" button on listings page
- **File**: `apps/web/src/app/dashboard/listings/page.tsx`
- Add button in header: "Scrape New Listings"
- Opens a modal/input for location + max results
- Calls `POST /api/v1/scrape` with auth token
- Shows loading state, then success toast with count
- Refreshes listing grid after import

### 3.4 Property detail page
- **File**: `apps/web/src/app/dashboard/listings/[id]/page.tsx` (new)
- **Layout**: Full-width image gallery at top (all property images, carousel or grid)
- **Info section**: Address, price, beds/baths/sqft, property type, status badge, year built, lot size, garage spaces, MLS number
- **AI description**: "Generate Description" button → calls `POST /api/v1/listings/{id}/generate-description`
- **Quick actions**: Schedule Showing, Compare Properties, Ask Athena
- **Backend**: `GET /api/v1/listings/{id}` already exists, returns full property

### 3.5 Wire up "Schedule Showing" from property detail + chat
- **Athena tool**: `schedule_showing` already exists (tools.py:564)
- **Frontend**: Add "Schedule Showing" button on property detail page → opens date/time picker + client name → calls schedule_showing through Athena chat or direct API
- **Calendar page**: Already reads from showings table. Events appear automatically.

### 3.6 Daily briefing + proactive recommendations
- **Briefing endpoint** `GET /briefing` already exists, uses `briefing.py` from `packages/ai/`
- Verify it returns sensible data with real DB data
- **Recommendations endpoint** `GET /api/v1/dashboard/recommendations` already has "get started" message for empty DB
- Add more recommendation types: hot leads need follow-up, stale leads need re-engagement, low inventory needs scraping

---

## Phase 4: Frontend Polish

### 4.1 Transform "AI Agents" → "Capabilities"
- **File**: `apps/web/src/app/dashboard/ai-agents/page.tsx` — rewrite
- Call `GET /api/v1/athena/state` to get `TOOL_DEFINITIONS` (25 tools)
- Group tools by category:
  - **Leads**: list_leads, get_lead_detail, update_lead_status, score_lead, analyze_pipeline, recommend_follow_up
  - **Listings**: list_listings, generate_listing_description, property_price_analysis, scrape_properties_advanced, scrape_and_import_properties, check_scraper_sources
  - **Market**: market_snapshot, compare_neighborhoods, market_trend_report
  - **Documents**: summarize_contract, extract_deadlines
  - **Marketing**: launch_campaign
  - **Scheduling**: schedule_showing
  - **Web**: browse_web_page, search_web
  - **Memory**: remember_fact, recall_memory, save_note
  - **System**: get_dashboard_summary, get_agent_stats, system_overview
- Display each tool with name, description, category badge
- Shows total tool count

### 4.2 Consolidate sidebar
- **File**: `apps/web/src/components/dashboard/sidebar.tsx`
- Primary links (always visible): Athena, Dashboard, Leads, Listings, Calendar, Documents, Settings
- "More" dropdown/expandable section: Analytics, Marketing, Memory, Capabilities
- Remove Docs link
- Keep Athena highlighted (amber)

### 4.3 Fix listing card thumbnails
- **File**: `apps/web/src/app/dashboard/listings/page.tsx` — `ListingCard`
- After pipeline fix (flat array), `image_url` from `normalizeProperty` should get `images[0]` correctly
- Verify: cards show real photos, not gradient fallback
- Add loading skeleton for images

### 4.4 Wire document Q&A to frontend
- **File**: `apps/web/src/app/dashboard/documents/page.tsx`
- Add "Ask about this document" button per document → opens inline chat with Athena pre-contextualized
- Use `POST /api/v1/documents/{id}/ask` endpoint (already exists)

---

## Phase 5: Verification

### 5.1 End-to-end test flow
1. Register new user → empty dashboard shows "get started" recommendation
2. Chat with Athena: "scrape 5 properties in Edmonton and import them"
3. Verify: images shown in chat response with `![alt](url)` → rendered as thumbnails
4. Verify: listing grid shows 5 cards with real photos
5. Click listing card → property detail page with image gallery
6. Generate MLS description → AI description appears
7. Chat: "score all my leads" → scores calculated
8. Leads kanban shows scored leads
9. Chat: "schedule a showing for [property] Friday at 2pm" → appears on calendar
10. Dashboard shows recommendations based on real data

### 5.2 Verification commands
```bash
# Backend parse check
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['packages/hermes/src/hermes/tools.py', 'packages/hermes/src/hermes/agent.py', 'apps/api/src/main.py', 'packages/hermes/src/hermes/scraper/zillow.py']]; print('All OK')"

# Health check
curl https://realty-ai-api-production.up.railway.app/health

# Deploy
railway up --detach
git push  # triggers Vercel
```

---

## Files to Modify/Create

| File | Action |
|------|--------|
| `packages/ai/crews/` | **Delete** directory |
| `packages/ai/agents/` | **Delete** directory |
| `packages/hermes/src/hermes/tools.py` | Remove crew tools, add 4 new tools, update tool count |
| `packages/hermes/src/hermes/agent.py` | Remove crew references from system prompt |
| `apps/api/src/main.py` | Remove `/ai`, `/supervisor/*` endpoints, update imports, update system-overview |
| `apps/api/src/api/v1/leads.py` | Add auto-scoring on create_lead |
| `apps/web/src/app/dashboard/listings/[id]/page.tsx` | **Create** — property detail page |
| `apps/web/src/app/dashboard/listings/page.tsx` | Add "Scrape New Listings" button |
| `apps/web/src/app/dashboard/ai-agents/page.tsx` | Rewrite → Capabilities page |
| `apps/web/src/components/dashboard/sidebar.tsx` | Consolidate to core 7 + More menu |
| `apps/web/src/app/dashboard/athena/page.tsx` | Verify renderMarkdown handles images |
| `apps/web/src/lib/api.ts` | Add auto-generated description to Property interface |

---

## Migration & Rollback

- **No DB migrations needed** — all changes are code-only
- **No data loss** — all existing DB data (leads, listings, users) preserved
- **Rollback**: revert git commits. No irreversible operations.
- **Frontend**: Vercel auto-deploys on push. Backend: Railway auto-deploys on push.
- **Deploy order**: Backend (Railway) must deploy first (new tools, removed endpoints). Frontend deploys second (new pages reference new API responses).
