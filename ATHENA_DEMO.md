# Athena — RealtyAI Digital Secretary

**Demo Walkthrough & System Architecture**

## Table of Contents
1. [Demo Quick Start](#demo-quick-start)
2. [Architecture Overview](#architecture-overview)
3. [User Experience](#user-experience)
4. [Key Features](#key-features)
5. [Web Scraping System](#web-scraping-system)
6. [Deployment](#deployment)
7. [Demo Account & URLs](#demo-account--urls)

---

## Demo Quick Start

### 1. Open the app
Navigate to **https://realty-ai-ten.vercel.app**

### 2. Sign in
- **Email:** `demo@realtyai.demo`
- **Password:** `Demo123!`

Alternatively, click **Sign Up** to create a new account (you'll get a fresh onboarding conversation with Athena).

### 3. Welcome to Athena
After login, you land on the dashboard. Click **Chat with Athena** in the sidebar to start a conversation.

### 4. Ask Athena anything
Try these demo prompts:

| Category | Prompt |
|----------|--------|
| **Getting Started** | "Hello Athena, what can you do?" |
| **Lead Management** | "Show me my lead pipeline" |
| **Listings** | "What properties are active right now?" |
| **Market Intelligence** | "Give me a market snapshot for Edmonton" |
| **Pipeline Analysis** | "Analyze my pipeline and tell me who to call first" |
| **Web Search** | "Search the web for Calgary market trends" |
| **Property Scraping** | "Scrape Edmonton listings from Zillow" |
| **Web Reading** | "Browse https://www.realtor.com for me" |
| **Documents** | "Summarize this contract: [paste contract text]" |
| **Campaigns** | "Launch a 'Summer Open House' campaign" |
| **Memory** | "Remember I prefer mornings for showings" |
| **System** | "Give me the full system overview" |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vercel (Frontend)                        │
│  Next.js 14 · Tailwind · motion · Geist Font                   │
│  /splash · /login · /signup · /dashboard/*                     │
│                                                                 │
│  Sidebar: Dashboard | Leads | Listings | Calendar |             │
│           Marketing | Documents | Settings | Chat               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / JWT Auth
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Railway (Backend API)                        │
│  FastAPI · SQLAlchemy · LangChain · Athena Agent                │
│                                                                 │
│  /api/v1/auth        — Login, Register, Profile                 │
│  /api/v1/athena/chat — AI chat with memory                      │
│  /api/v1/dashboard   — Summary, Recommendations                 │
│  /api/v1/calendar    — Events from showings                     │
│  /api/v1/campaigns   — Marketing campaigns                      │
│  /api/v1/scrape      — Trigger property scraper                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────┐
│   PostgreSQL    │ │  Mem0    │ │  Free LLM    │
│  (Railway)      │ │ (Memories)│ │  Pool        │
│  properties     │ │          │ │  deepseek-v4  │
│  leads          │ │          │ │  mimo-v2.5    │
│  campaigns      │ │          │ │  opencode-zen │
│  showings       │ │          │ │               │
│  documents      │ │          │ │               │
│  activities     │ │          │ │               │
│  conversations  │ │          │ │               │
└─────────────────┘ └──────────┘ └──────────────┘
```

### AI Architecture

```
Athena Agent (LangChain tool-calling)
├── Tools (20 tools)
│   ├── Leads: list, detail, update status, pipeline analysis
│   ├── Listings: list, describe, compare, market snapshot
│   ├── Marketing: launch campaigns, generate descriptions
│   ├── Documents: summarize contracts, extract deadlines
│   ├── Memory: remember facts, recall, save notes
│   ├── Scheduling: showings
│   ├── Crew: get crew info, run specialist crews
│   └── 🌐 Web: browse pages, search web, advanced scraping
│
├── Multi-Source LLM (free provider pool)
│   ├── Tier 0: opencode-zen (deepseek-v4-flash-free)
│   ├── Tier 1: 9router tunnel (mimo-v2.5-free)
│   ├── Tier 2: featherless
│   └── Tier 3: nvidia (fallback)
│
├── Persistent Memory
│   ├── SQLite + FTS5 (local facts & notes)
│   ├── Mem0 (semantic memory layer)
│   └── PostgreSQL conversations (per-user threads)
│
└── Scraping System
    ├── ZillowScraper (requests-based, static pages)
    ├── ObscuraScraper (Rust headless browser, 85ms pages)
    ├── BrowserUseScraper (Python browser automation, JS rendering)
    ├── AgentReachConnector (15+ platforms, web search)
    └── SuperScraper (unified orchestrator)
```

---

## User Experience

### Splash Page (https://realty-ai-ten.vercel.app)
- Premium animated SVG hero with orbital rings, data streams, particles
- Compliance section (OREA, RESPA, TREC badges)
- 5 feature cards: Lead Management, AI Listings, Compliance, Market Intel, Memory
- Demo access section with urgency messaging
- Indications Media branding in footer

### Onboarding (New Users)
When a new user says hello, Athena:
1. Warmly introduces herself
2. Asks for the user's name
3. Gives a full capabilities breakdown (leads, listings, documents, calendar, marketing, market intel, memory, compliance)
4. Asks what they'd like to tackle first

### Dashboard
- Greeting reads the user's name from localStorage
- Stats cards: Total Leads, Active Listings, Hot Leads, Pipeline Value
- Recent activity feed
- Quick action buttons

### Chat Interface
- Per-user conversation threads (isolated memory)
- Tool-calling responses with structured data
- Fallback response builder (never drops tool results)
- Relationship-building personality

---

## Key Features

### Per-User Memory Isolation
Every user gets:
- Separate conversation thread in PostgreSQL (`athena_conversations`)
- Scoped messages (`athena_chat_messages` by user_id)
- Isolated facts and notes (`athena_facts`, `athena_notes`)
- Independent Mem0 memory space
- Memory reset via `/api/v1/athena/reset-memory`

### 20 Agent Tools

| Category | Tools |
|----------|-------|
| **Leads** | list_leads, get_lead_detail, update_lead_status, analyze_pipeline |
| **Listings** | list_listings, generate_listing_description, market_snapshot, compare_neighborhoods |
| **Marketing** | launch_campaign |
| **Documents** | summarize_contract, extract_deadlines |
| **Memory** | remember_fact, recall_memory, save_note |
| **Scheduling** | schedule_showing |
| **Crew** | get_crew_info, run_crew (6 specialist crews) |
| **System** | get_dashboard_summary, get_agent_stats, system_overview |
| **🌐 Web** | browse_web_page, search_web, scrape_properties_advanced, check_scraper_sources |

### Compliance Awareness
- Canadian real estate law (OREA, TREC, provincial acts)
- US regulations (RESPA, licensing, disclosure)
- Disclaimer: "Always consult a qualified lawyer"
- Contract risk flagging in summarization

---

## Web Scraping System

Athena has a multi-source scraping system that aggregates data from four independent tools:

### 1. ZillowScraper (requests-based)
- Static HTTP requests to Zillow search pages
- 3 extraction strategies: catZillowSearchResults → Apollo state → script tags
- Fallback generator for demo reliability
- **Always available** (pure Python, no extra installs)

### 2. ObscuraScraper (Rust headless browser)
- **Repo:** https://github.com/h4ckf0r0day/obscura (19.7k stars)
- Ultra-lightweight: 30MB memory, 85ms page loads
- Built-in stealth mode (anti-fingerprinting + tracker blocking)
- CDP-compatible (works with Puppeteer/Playwright)
- Ships MCP server for AI agent integration
- **Install:** Download binary from releases page, place on PATH or set `OBSCURA_PATH`

### 3. BrowserUseScraper (Python browser automation)
- **Repo:** https://github.com/browser-use/browser-use (106k stars)
- Full browser control: clicks, types, scrolls, reads rendered DOM
- Uses Playwright under the hood for real browser automation
- Handles JS-heavy pages that static requests miss
- **Install:** `pip install browser-use && playwright install chromium`

### 4. AgentReachConnector (platform connectivity)
- **Repo:** https://github.com/Panniantong/Agent-Reach (60.6k stars)
- 15+ platforms: web pages, YouTube, GitHub, Twitter/X, Reddit, Bilibili, RSS, Exa search, LinkedIn, Instagram, Facebook, Xiaohongshu
- Automatic backend routing (swaps dead CLIs for working ones)
- Health checks via `agent-reach doctor`
- Exa semantic web search (free, no API key via MCP)
- **Install:** `pip install agent-reach && agent-reach install --env=auto`

### 5. Hermes Browser Extension (real-time context)
- **Repo:** https://github.com/abundantbeing/hermes-browser-extension (1.1k stars)
- Chrome/Edge side panel for real-time browser context capture
- Connects to local Hermes gateway (http://127.0.0.1:8642)
- Passive read-only: no autonomous browser control
- Provides: page title/URL, readable text, open tabs, selected text
- **Install:** Clone repo, `npm install && npm run build`, load `dist/` unpacked

### SuperScraper Orchestrator
The **SuperScraper** class tries all sources in order:
1. ZillowScraper (requests, fastest)
2. Obscura (85ms stealth headless)
3. Browser-Use (full JS rendering, most capable)
4. Agent-Reach (web search fallback)

Results are deduplicated by address and merged. Athena calls this via the `scrape_properties_advanced` tool.

### Check Sources
Use `check_scraper_sources` to see what's installed:
```
✅ zillow_requests
✅ obscura
❌ browser_use
✅ agent_reach
```

---

## Deployment

### Backend (Railway)
- **URL:** https://realty-ai-api-production.up.railway.app
- **Stack:** FastAPI, SQLAlchemy, LangChain
- **Database:** PostgreSQL (managed by Railway)
- **Memory:** Local SQLite + Mem0 (per-user)

### Frontend (Vercel)
- **URL:** https://realty-ai-ten.vercel.app
- **Stack:** Next.js 14, Tailwind, motion, Geist font
- **Pages:** Splash, Login, Signup, Dashboard (7 sub-pages)

### Environment Variables
```
# .env (required)
DATABASE_URL=postgresql+asyncpg://...
OPENCODE_ZEN_API_KEY=sk-zen-free
OPENCODE_ZEN_API_BASE=https://opencode.ai/zen/v1
ATHENA_MODEL=deepseek-v4-flash-free
JWT_SECRET=your-secret-key

# Optional (for web scraping)
OBSCURA_PATH=/usr/local/bin/obscura
```

### Free LLM Provider Pool
| Provider | Base URL | Models |
|----------|----------|--------|
| opencode-zen | https://opencode.ai/zen/v1 | deepseek-v4-flash-free, mimo-v2.5-free |
| 9router | (dynamic) | deepseek-v4-flash-free, mimo-v2.5-free |
| featherless | (dynamic) | Various free models |
| nvidia | https://integrate.api.nvidia.com/v1 | Various free models |

The `ResilientLLM` class rotates across providers and falls through on ANY failure (timeout, 429, 5xx, auth).

---

## Demo Account & URLs

| Resource | URL / Credentials |
|----------|-------------------|
| **Frontend** | https://realty-ai-ten.vercel.app |
| **Backend API** | https://realty-ai-api-production.up.railway.app |
| **Demo Email** | `demo@realtyai.demo` |
| **Demo Password** | `Demo123!` |
| **Health Check** | `GET /health` |
| **API Docs** | `GET /docs` (Swagger UI) |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Login (returns JWT) |
| PUT | /api/v1/auth/profile | Update profile |
| POST | /api/v1/athena/chat | Chat with Athena |
| POST | /api/v1/athena/reset-memory | Wipe user memory |
| GET | /api/v1/dashboard/recommendations | AI recommendations |
| GET | /api/v1/calendar/events | Calendar events |
| GET | /api/v1/campaigns | Marketing campaigns |
| POST | /api/v1/scrape | Trigger scraper |

---

## Future Enhancements

1. **Wire Settings save** → frontend POST to `/api/v1/auth/profile`
2. **Wire Dashboard recommendations** → fetch from API endpoint
3. **Wire Documents icons** → sparkle (AI summary) + download handlers
4. **Install Obscura on Railway** → add binary and enable stealth
5. **Install Browser-Use** → `pip install browser-use` + Playwright
6. **Install Agent-Reach** → enables 15+ platforms
7. **Hermes Browser Extension** → real-time browser context for Athena
8. **Run scraper against Railway DB** → populate real property/lead data
9. **Daily market briefing** → automatically scraped and summarized by Athena

---

*Built by **Indications Media** with Athena AI*