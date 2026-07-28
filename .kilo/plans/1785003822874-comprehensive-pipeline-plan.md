# RealtyAI — Comprehensive Plan: End-to-End Scrape Pipeline + Realtor-Ready Features

## Current State (What Works)

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend pages (10 dashboard + landing + docs) | ✅ | All load, UI structure complete |
| Auth (register/login/JWT) | ✅ | Working end-to-end |
| Athena AI Chat (DeepSeek v4 Flash) | ✅ | Tool calling, memory, conversation persistence |
| Zillow scraper (Jina Reader) | ✅ | Returns 9-25 real listings with address/price/beds/baths/sqft/url |
| Frontend ListingCard (image + price + address + badges) | ✅ | UI ready, needs DB data |
| Lead management API (CRUD + scoring) | ✅  | Full API, frontend Kanban ready |
| Dashboard recommendations | ✅ | Working with CORS fix |
| CORS / deps fix | ✅ | Deployed, dashboard returns 200 |
| Listings API (CRUD) | ✅ | Working but DB is empty |
| bot integrations (Telegram, Slack) | ✅ | Webhooks + config UI |

## What's Broken (Blocks Pipeline)

| Issue | File | Fix |
|-------|------|-----|
| Postgres enum `property_type` uses `SINGLE_FAMILY` (uppercase), scraper sends `single_family` | `zillow.py:134,205` | ✅ Fixed in commit `a2595d5`, not yet deployed |
| Postgres enum `property_status` uses `ACTIVE` (uppercase), scraper sends `active` | `zillow.py:135,205` | ✅ Fixed, not deployed |
| Address extraction returns empty — `"zillow" in line` check filters out lines with embedded URLs | `zillow.py:233-235` | ✅ Fixed, not deployed |
| Transaction aborted after first failed INSERT — no rollback in except block | `pipeline.py:86` | ✅ Fixed (rollback added), not deployed |
| Images not extracted from Jina output — `_extract_img` regex doesn't match Jina's `![alt](url)` format | `zillow.py:249-252` | ❌ Not yet fixed — parser uses old pattern |
| SuperScraper mixes agent-reach placeholder data ("Web Search Results", $0) | `tools.py:1057` | ❌ `_scrape_properties_advanced` uses SuperScraper, not ZillowScraper directly |
| Frontend `renderMarkdown()` doesn't render links or images | `page.tsx:52` | ✅ Fixed in commit `405bde0`, not deployed |
| DB `images` column stores `{"source": "zillow", "images": []}` — empty array | `pipeline.py:63` | ❌ Scraper not extracting images into listing dicts |

## Phase 1: End-to-End Scrape Pipeline (P0)

**Goal:** `scrape properties in Edmonton` → real listings with thumbnails + links in chat → imported to DB → visible on listings dashboard.

### 1.1 Fix Jina Reader Image Extraction
- **File:** `packages/hermes/src/hermes/scraper/zillow.py`
- `_extract_img` (line 249): Update regex to match `![alt](img_url)` and `[![alt](img_url)](url)` formats
- The Jina output format is `[![Image 5: address](https://photos.zillowstatic.com/...)](detail_url)` — need to extract the inner `(url)` inside `![]()()` nested parentheses
- After fix: `images: ["https://photos.zillowstatic.com/...", ...]` (1-3 per listing)

### 1.2 Consolidate Display Functions on ZillowScraper Directly
- **File:** `packages/hermes/src/hermes/tools.py`
- `_scrape_properties_advanced` (line 1057): Replace SuperScraper call with direct `ZillowScraper().search()` to avoid agent-reach pollution
- `_scrape_and_import` (line 1141): Already uses `ZillowScraper` + `scrape_and_seed` — keep this
- Display output: `$PRICE | beds bd | baths ba | sqft sqft` + `![thumbnail](image)` + `[View on Zillow](url)`

### 1.3 Verify All Fixes Deploy & Pipeline Works
- Deploy commits `a2595d5` (enum fix) and `405bde0` (frontend markdown) + image extraction fix
- Test: `scrape properties in Edmonton under $500k`
- Verify: 5+ listings with real addresses, prices, thumbnails displayed in chat
- Verify: Properties inserted into DB (dashboard shows count > 0)
- Verify: Listings dashboard page loads with cards showing images

### 1.4 Add "Import" Button on Listings Dashboard
- **File:** `apps/web/src/app/dashboard/listings/page.tsx`
- Add "Scrape New Listings" button in the header that calls `POST /api/v1/scrape`
- Show loading spinner and success toast with count imported
- This gives realtors a direct way to refresh listings without going through chat

### 1.5 Fix Listing Card Thumbnail
- **File:** `apps/web/src/lib/api.ts` (normalizeProperty, line 185)
- `image_url` already maps `images[0]` — but the DB stores images as a JSON object `{"source":..., "images":[...], "url":...}`, not a plain array
- Fix: extract the inner `images` array from the JSONB object, or change the DB insert to store images as a flat array
- **File:** `packages/hermes/src/hermes/scraper/pipeline.py` (line 56-63)
- Change images storage: store as JSON array `["url1", "url2", "url3"]` directly in the `images` JSONB column, not wrapped in a dict

---

## Phase 2: Lead Management + AI Scoring (P1)

**Goal:** Realtors can view, score, and manage leads generated from scraped property interest.

### 2.1 Seed Pipeline Output to Generate Leads
- **File:** `packages/hermes/src/hermes/scraper/pipeline.py`
- Add `_generate_leads()` back (was removed) — but only if user opts in via a tool parameter `generate_leads=true`
- Each lead = buyer persona interested in a specific property type/price range/location
- Scoped to the requesting user's `agent_id`
- Default: no lead generation (only properties)

### 2.2 Fix Lead Dashboard to Show Real Data
- **File:** `apps/web/src/app/dashboard/leads/page.tsx`
- Already has Kanban columns, score badges, detail popup
- Verify: columns populate with DB data after lead generation
- Verify: scoring endpoint `PATCH /api/v1/leads/{id}/score` returns sensible scores

### 2.3 Add Lead Creation from Chat
- When Athena scrapes, offer: _"I found X properties. Would you like me to create buyer leads from these?"_
- Athena calls `scrape_and_import_properties` with `generate_leads=true`
- Leads appear in the leads pipeline immediately

---

## Phase 3: Multi-Tenant Data Isolation (P1)

**Goal:** Each realtor sees only their own data. New signup gets a clean slate.

### 3.1 Complete User-Scoping Audit
- **File:** `apps/api/src/api/v1/` — all routers
- Verify every GET/POST/PUT/DELETE uses `current_user.sub` to filter/set `agent_id`
- Dashboard summary: ✅ already scoped
- Leads: add `WHERE agent_id = :uid` to list/get/stats
- Listings: add `WHERE agent_id = :uid` to list/get
- Documents: add `WHERE agent_id = :uid`
- Campaigns: add `WHERE user_id = :uid`
- Calendar events: add `WHERE user_id = :uid`

### 3.2 Scoped Chat Memory
- **File:** `packages/hermes/src/hermes/agent.py`
- `get_or_create_active_conversation(user_id)` already scoped
- `profile_summary()`, `recall()`, `save_conversation()` — verify user_id filters
- Mem0 adapter: already passes `user_id`

### 3.3 Fresh Signup Experience
- **File:** `apps/web/src/app/dashboard/page.tsx`
- New user sees: empty dashboard with welcoming message _"Welcome, [name]! Get started by scraping properties in your area."_
- CTA button: "Scrape Listings" → triggers scrape
- No leaked data from other users

### 3.4 Remove Old Seed/Demo Data
- **File:** `apps/api/src/main.py` (`/api/v1/seed` endpoint) — already gutted, no demo data
- **DB:** Existing demo data must be manually deleted via API or SQL

---

## Phase 4: Daily Briefing + AI Recommendations (P2)

**Goal:** Morning briefing with personalized data. AI-powered action items.

### 4.1 Personalized Briefing
- **File:** `apps/api/src/main.py` — `GET /briefing`
- `current_user.name` passed to `generate_briefing(agent_name=name)` — ✅ fixed
- `_lead_briefing()` and `_listing_briefing()` query DB with scoped user data
- Output: greeting by name, hot leads, active listings, suggested actions

### 4.2 Auto-Generated Dashboard Recommendations
- **File:** `apps/api/src/main.py` — `GET /api/v1/dashboard/recommendations`
- Already scoped by `agent_id` — ✅
- Verify: returns sensible recommendations when data exists
- Add: "No recent activity — scrape below-market listings in your area" when DB is empty

### 4.3 Athena Proactive Check-Ins
- **File:** `packages/hermes/src/hermes/agent.py` (system prompt)
- Add: _"At startup of each conversation, scan the user's dashboard and mention 1-2 observations."_
- Athena already has this behavior via periodic snapshot injection (lines 532-541)

---

## Phase 5: Calendar + Showings (P2)

**Goal:** Schedule showings from scraped properties. Calendar view with events.

### 5.1 Fix Calendar Data Source
- **File:** `apps/web/src/app/dashboard/calendar/page.tsx`
- Already has monthly view, event cards, color coding
- Events come from `GET /api/v1/calendar/events` → `showings` table
- Showings table is empty — need to populate via chat
- Athena tool: `schedule_showing(lead_name, property_address, time)` ✅ exists

### 5.2 Connect Scrape → Showing
- After scraping, Athena offers: _"Schedule a showing for any of these properties. Just tell me which one and when."_
- User: "Schedule showing for 17951 80th Ave this Friday at 2pm"
- Athena calls `schedule_showing` → inserts into showings table → appears on calendar

### 5.3 Calendar Frontend Improvements
- Add "Showing" as clickable event → opens property detail card
- Color-code: showing=blue, open house=green, closing=orange, meeting=purple
- Add "+ Schedule" button on listing cards in the dashboard

---

## Deployment & Verification

After each phase, verify:
1. `bash deploy.sh` → backend deploys via Docker
2. Vercel auto-deploys frontend
3. `curl` test the API endpoints
4. Browser test at `realty-ai-ten.vercel.app` or `realty.indicationsmedia.com`
5. Test with fresh signup account (no data leaks)

### Key File Reference

| File | Purpose |
|------|---------|
| `packages/hermes/src/hermes/scraper/zillow.py` | Zillow/Jina Reader scraper |
| `packages/hermes/src/hermes/scraper/pipeline.py` | DB insert pipeline |
| `packages/hermes/src/hermes/tools.py` | Athena tool implementations |
| `packages/hermes/src/hermes/agent.py` | Athena agent, LLM config |
| `apps/api/src/main.py` | All API endpoints |
| `apps/api/src/api/v1/` | REST API routers |
| `apps/web/src/app/dashboard/` | Frontend dashboard pages |
| `apps/web/src/lib/api.ts` | Frontend API types + normalize |
| `apps/web/src/app/dashboard/athena/page.tsx` | Chat UI + markdown renderer |
| `packages/ai/free_llm.py` | LLM provider config |
| `packages/database/src/models/` | ORM models |
