# RealtyAI V1 — Architecture & Implementation Plan

## Decisions

| Decision | Choice |
|----------|--------|
| Repository | New GitHub repo, clean break from current monorepo |
| LLM | DeepSeek Flash V4 only — no fallback chain |
| Embeddings | bge-small-en-v1.5 via fastembed (384 dims) |
| Vector store | pgvector in PostgreSQL — replaces Mem0/Qdrant/SQLite |
| Background jobs | Redis + Celery |
| Frontend | Full rebuild: Next.js 15 + Zustand + TanStack Query + shadcn/ui |
| Chat agent | Athena preserved as conversational interface, wraps new services |
| Scraping | Port Zillow scraper into V1 |
| Legacy features preserved | Chat agent + property scraping only |
| Auth | JWT for V1, OAuth-ready for Phase 2 |

## Philosophy

> "DeepSeek is the reasoning engine. The application is the operating system."

Rule: DeepSeek makes decisions. Software executes them. Never call DeepSeek from frontend. All AI communication goes through `AIService`.

---

## Project Structure

```
realty-ai-v1/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, router registration, middleware
│   │   ├── config.py                # Settings via pydantic-settings
│   │   ├── deps.py                  # FastAPI dependency injection
│   │   ├── api/
│   │   │   ├── router.py            # Prefix /api/v1
│   │   │   ├── auth.py              # POST /register, /login, /me
│   │   │   ├── clients.py           # CRUD /clients
│   │   │   ├── messages.py          # /messages (email/SMS inbound)
│   │   │   ├── tasks.py             # /tasks
│   │   │   ├── listings.py          # /listings + /scrape
│   │   │   ├── chat.py              # /chat (Athena interface)
│   │   │   ├── briefing.py          # /briefing
│   │   │   ├── memory.py            # /memories search/CRUD
│   │   │   ├── search.py            # /search (keyword + semantic)
│   │   │   └── integrations.py      # OAuth connect, webhooks
│   │   ├── services/
│   │   │   ├── base.py              # BaseService with DB session
│   │   │   ├── auth_service.py      # JWT, password hashing, user CRUD
│   │   │   ├── client_service.py    # Client CRUD, relationship mgmt
│   │   │   ├── ai_service.py        # DeepSeek calls, prompt templates, structured outputs
│   │   │   ├── memory_service.py    # pgvector operations, fact extraction, retrieval
│   │   │   ├── communication_service.py  # Email/SMS inbound/outbound, message pipeline
│   │   │   ├── task_service.py      # Task CRUD, AI-generated tasks
│   │   │   ├── listing_service.py   # Property CRUD, Zillow scraper
│   │   │   ├── briefing_service.py  # Daily briefing generation
│   │   │   └── search_service.py    # Keyword + semantic search
│   │   ├── models/
│   │   │   ├── base.py              # SQLAlchemy Base + mixins (UUID pk, timestamps, soft delete)
│   │   │   ├── user.py
│   │   │   ├── client.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── memory.py            # pgvector embedding column
│   │   │   ├── task.py
│   │   │   ├── property.py
│   │   │   ├── integration.py
│   │   │   └── ai_log.py            # AIInteractionLog
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── client.py
│   │   │   ├── message.py
│   │   │   ├── task.py
│   │   │   ├── listing.py
│   │   │   ├── chat.py
│   │   │   ├── briefing.py
│   │   │   ├── memory.py
│   │   │   └── search.py
│   │   ├── prompts/
│   │   │   ├── analyze_message.txt
│   │   │   ├── extract_memory.txt
│   │   │   ├── generate_reply.txt
│   │   │   ├── generate_briefing.txt
│   │   │   ├── summarize_conversation.txt
│   │   │   └── athena_system.txt    # Athena chat system prompt
│   │   ├── worker/
│   │   │   ├── celery_app.py        # Celery app config
│   │   │   └── tasks.py             # Async tasks (email sync, embeddings, briefing)
│   │   └── embeddings/
│   │       └── embedder.py          # fastembed wrapper (bge-small)
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_clients.py
│       ├── test_ai_service.py
│       ├── test_memory.py
│       └── test_briefing.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (providers)
│   │   │   ├── page.tsx             # Redirect to /dashboard
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx       # Dashboard shell (sidebar + header)
│   │   │       ├── page.tsx         # Overview (stats, briefing, activity)
│   │   │       ├── chat/            # Athena chat interface
│   │   │       ├── clients/         # Client list + detail + create
│   │   │       ├── listings/        # Property listings + scrape
│   │   │       ├── tasks/           # Task board
│   │   │       ├── messages/        # Inbound messages (email/SMS)
│   │   │       ├── memory/          # Client memory browser
│   │   │       ├── search/          # Global search
│   │   │       ├── settings/        # User + integrations settings
│   │   │       └── briefing/        # Daily briefing history
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui primitives
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── header.tsx
│   │   │   ├── chat/
│   │   │   │   ├── chat-input.tsx
│   │   │   │   ├── chat-message.tsx
│   │   │   │   └── chat-history.tsx
│   │   │   ├── clients/
│   │   │   │   ├── client-card.tsx
│   │   │   │   ├── client-detail.tsx
│   │   │   │   └── client-memories.tsx
│   │   │   └── shared/
│   │   │       ├── loading-skeleton.tsx
│   │   │       ├── error-card.tsx
│   │   │       └── empty-state.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Axios/fetch API client
│   │   │   ├── auth.ts              # JWT storage, token refresh
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   ├── use-clients.ts       # TanStack Query hooks
│   │   │   ├── use-tasks.ts
│   │   │   ├── use-messages.ts
│   │   │   ├── use-memories.ts
│   │   │   ├── use-listings.ts
│   │   │   ├── use-briefing.ts
│   │   │   ├── use-chat.ts
│   │   │   └── use-search.ts
│   │   ├── stores/
│   │   │   ├── auth-store.ts        # Zustand auth state
│   │   │   └── ui-store.ts          # Sidebar, theme, preferences
│   │   └── types/
│   │       ├── client.ts
│   │       ├── message.ts
│   │       ├── task.ts
│   │       ├── listing.ts
│   │       ├── chat.ts
│   │       ├── memory.ts
│   │       └── search.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.js
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.worker
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
└── README.md
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | VARCHAR(255) UNIQUE | |
| password_hash | VARCHAR(255) | bcrypt |
| full_name | VARCHAR(255) | |
| phone | VARCHAR(50) | nullable |
| avatar_url | VARCHAR(500) | nullable |
| brokerage_name | VARCHAR(255) | nullable |
| license_number | VARCHAR(100) | nullable |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |
| deleted_at | TIMESTAMPTZ | soft delete |

### `clients`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | agent who owns |
| name | VARCHAR(255) | |
| email | VARCHAR(255) | nullable |
| phone | VARCHAR(50) | nullable |
| client_type | VARCHAR(20) | buyer, seller, both |
| status | VARCHAR(20) | active, inactive, closed, lost |
| budget_min | INTEGER | nullable |
| budget_max | INTEGER | nullable |
| location_interest | JSONB | `["Edmonton", "Calgary"]` |
| property_type_interest | VARCHAR(50) | nullable |
| features_wanted | JSONB | `["garage", "pool"]` |
| timeline | VARCHAR(50) | immediate, 1-3mo, 3-6mo, 6mo+ |
| pre_approved | BOOLEAN | |
| notes | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

### `conversations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| client_id | UUID FK→clients | nullable |
| title | VARCHAR(255) | |
| status | VARCHAR(20) | active, closed |
| platform | VARCHAR(20) | chat, email, sms |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

### `messages`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| conversation_id | UUID FK→conversations | |
| role | VARCHAR(20) | user, assistant, system |
| content | TEXT | |
| direction | VARCHAR(10) | inbound, outbound |
| platform | VARCHAR(20) | chat, email, sms |
| metadata | JSONB | raw provider data |
| created_at | TIMESTAMPTZ | |

### `memories`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| client_id | UUID FK→clients | |
| category | VARCHAR(50) | identity, preference, fact, event, concern |
| content | TEXT | "John wants a garage" |
| source | VARCHAR(255) | "Email conversation July 12" |
| confidence | FLOAT | 0.0 - 1.0 |
| importance | INTEGER | 0-100 |
| embedding | vector(384) | bge-small |
| metadata | JSONB | |
| expires_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

Indexes:
- HNSW index on `embedding` for cosine similarity
- BTREE on `(user_id, client_id)`
- BTREE on `(user_id, category)`

### `tasks`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| client_id | UUID FK→clients | nullable |
| title | VARCHAR(500) | |
| description | TEXT | nullable |
| priority | VARCHAR(10) | high, medium, low |
| status | VARCHAR(20) | pending, in_progress, completed, cancelled |
| source | VARCHAR(50) | ai_generated, manual, message_driven |
| source_message_id | UUID FK→messages | nullable — which message triggered this |
| due_date | TIMESTAMPTZ | nullable |
| completed_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

### `properties`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| address_street | VARCHAR(500) | |
| address_city | VARCHAR(200) | |
| address_state | VARCHAR(100) | |
| address_zip | VARCHAR(20) | |
| list_price | INTEGER | |
| beds | INTEGER | |
| baths | FLOAT | |
| sqft | INTEGER | |
| property_type | VARCHAR(50) | |
| status | VARCHAR(50) | active, pending, sold |
| year_built | INTEGER | nullable |
| lot_size | FLOAT | nullable |
| description | TEXT | nullable |
| features | JSONB | |
| images | JSONB | array of URLs |
| url | VARCHAR(1000) | Zillow URL |
| source | VARCHAR(50) | zillow, manual |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

### `integrations`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| provider | VARCHAR(50) | gmail, outlook, twilio |
| access_token | TEXT | encrypted |
| refresh_token | TEXT | encrypted |
| token_expires | TIMESTAMPTZ | |
| config | JSONB | provider-specific settings |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | |

### `ai_interaction_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| operation | VARCHAR(100) | analyze_message, generate_reply, etc |
| model | VARCHAR(100) | deepseek-v4-flash |
| input_tokens | INTEGER | |
| output_tokens | INTEGER | |
| latency_ms | INTEGER | |
| prompt_hash | VARCHAR(64) | SHA256 of prompt template |
| success | BOOLEAN | |
| error | TEXT | nullable |
| created_at | TIMESTAMPTZ | |

---

## API Design

Base URL: `http://localhost:8000/api/v1`

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Login → JWT |
| GET | /auth/me | Required | Current user |
| PUT | /auth/profile | Required | Update profile |

### Clients
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /clients | Required | List/search clients |
| POST | /clients | Required | Create client |
| GET | /clients/{id} | Required | Client detail |
| PUT | /clients/{id} | Required | Update client |
| DELETE | /clients/{id} | Required | Soft delete |
| GET | /clients/{id}/memories | Required | Client's memories |
| GET | /clients/{id}/conversations | Required | Client's conversations |

### Messages (Inbound Communication)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /messages | Required | List messages (filters: client, platform, date) |
| GET | /messages/{id} | Required | Message detail |
| POST | /messages/webhook/gmail | Service | Gmail push notification webhook |
| POST | /messages/webhook/outlook | Service | Outlook subscription webhook |
| POST | /messages/webhook/twilio | Service | Twilio SMS webhook |

### Chat (Athena)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /chat | Required | Send message to Athena |
| GET | /chat/conversations | Required | List conversations |
| GET | /chat/conversations/{id} | Required | Get conversation messages |
| POST | /chat/conversations/new | Required | Start new conversation |

### Tasks
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /tasks | Required | List tasks (filters: status, priority, client) |
| POST | /tasks | Required | Create task |
| PUT | /tasks/{id} | Required | Update task |
| DELETE | /tasks/{id} | Required | Delete task |
| POST | /tasks/{id}/complete | Required | Mark complete |
| POST | /tasks/{id}/readdress | Required | AI-suggest next steps |

### Listings + Scraping
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /listings | Required | List properties |
| GET | /listings/{id} | Required | Property detail |
| POST | /listings | Required | Create manually |
| POST | /scrape | Required | Scrape Zillow for location |

### Briefing
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /briefing | Required | Today's briefing |
| GET | /briefing/history | Required | Past briefings |

### Memory
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /memories | Required | List all memories |
| GET | /memories/search | Required | Semantic search (?q=wants acreage) |
| GET | /memories/{id} | Required | Memory detail |
| DELETE | /memories/{id} | Required | Delete memory |

### Search
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /search | Required | Global search (?q=... returns clients, memories, messages, tasks) |

### Integrations
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /integrations | Required | List integrations |
| POST | /integrations/gmail/connect | Required | Start OAuth flow |
| GET | /integrations/gmail/callback | No | OAuth callback |
| POST | /integrations/outlook/connect | Required | Start OAuth flow |
| GET | /integrations/outlook/callback | No | OAuth callback |
| PUT | /integrations/{id} | Required | Update integration config |
| DELETE | /integrations/{id} | Required | Disconnect integration |

---

## Service Layer Design

### `AIService` (DeepSeek only)
```python
class AIService:
    """Single entry point for all DeepSeek calls."""
    
    def __init__(self, api_key: str, model: str = "deepseek-v4-flash"):
        ...
    
    def analyze_message(self, message: Message, client_context: dict) -> MessageAnalysis:
        """Extract intent, sentiment, tasks, memories from a message.
        Returns structured JSON via model's json_object mode."""
        ...
    
    def extract_memories(self, messages: list[Message], client_id: str) -> list[MemoryExtraction]:
        """Extract facts about client from conversation."""
        ...
    
    def generate_reply(self, message: Message, client_context: dict) -> ReplyDraft:
        """Draft a professional reply."""
        ...
    
    def generate_briefing(self, user_id: str) -> Briefing:
        """Generate daily briefing from tasks, messages, deadlines."""
        ...
    
    def chat(self, messages: list[dict], system_prompt: str, tools: list[dict]) -> ChatResponse:
        """Athena chat interface. Single-turn tool-calling."""
        ...
    
    def summarize_conversation(self, messages: list[Message]) -> str:
        """Summarize a client conversation thread."""
        ...
```

All methods:
1. Build a prompt from `prompts/*.txt` templates
2. Inject context (memories, client data, conversation history)
3. Call DeepSeek with structured output format
4. Parse and validate the JSON response
5. Log to `ai_interaction_logs`

### `MemoryService`
```python
class MemoryService:
    """PostgreSQL + pgvector memory system."""
    
    def store(self, user_id, client_id, content, category, source, confidence) -> Memory:
        """Store a memory with embedding."""
        ...
    
    def semantic_search(self, user_id, query, limit=10) -> list[Memory]:
        """Cosine similarity search via pgvector."""
        ...
    
    def get_client_memories(self, client_id) -> list[Memory]:
        """All memories for a client."""
        ...
    
    def get_context_for_ai(self, client_id, limit=10) -> str:
        """Formatted string of top memories for AI prompt injection."""
        ...
    
    def extract_and_store(self, messages, client_id) -> list[Memory]:
        """Call AI to extract facts, embed them, store them."""
        ...
```

### `CommunicationService`
```python
class CommunicationService:
    """Email + SMS ingestion pipeline."""
    
    def process_inbound(self, platform, raw_message) -> Message:
        """Full pipeline: store → analyze → extract tasks → extract memories."""
        ...
    
    def sync_email(self, user_id, provider="gmail"):
        """Background task: poll Gmail/Outlook for new messages."""
        ...
```

### Inbound Message Pipeline
```
Incoming message (email/SMS webhook)
  → CommunicationService.process_inbound()
    → DB: store message
    → MemoryService: retrieve client context
    → ConversationService: get recent history
    → AIService.analyze_message()
      → returns: intent, sentiment, extracted_tasks, extracted_memories, reply_draft
    → TaskService: create AI-suggested tasks
    → MemoryService: store extracted memories
    → Return: analysis + proposed actions
```

---

## Athena Chat Architecture

Athena layers:
1. **Retrieval**: Load client context, memories, recent messages
2. **Prompt assembly**: System prompt + retrieved context + tool definitions + history
3. **DeepSeek call**: Tool-calling mode with structured output
4. **Tool execution**: Executes tool calls (list clients, search memory, scrape properties, etc.)
5. **Response synthesis**: Clean output to frontend

Tools (Athena has access to via function calling):
- `list_clients(search)` → search clients by name
- `get_client(id)` → full client profile + memories
- `search_memories(query)` → semantic memory search
- `list_tasks(status, client_id)` → task list
- `create_task(title, client_id, priority)` → create task
- `list_properties(filters)` → property listings
- `scrape_properties(location, count)` → Zillow scraper
- `get_daily_briefing()` → today's briefing
- `draft_reply(client_id, context)` → AI drafts a reply
- `summarize_conversation(client_id)` → chat summary

---

## Embedding Pipeline

`embeddings/embedder.py`:
```python
from fastembed import TextEmbedding

class Embedder:
    def __init__(self, model="BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model)
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns 384-dim vectors."""
        ...
    
    def embed_query(self, text: str) -> list[float]:
        """Single 384-dim vector for search queries."""
        ...
```

Used by:
- `MemoryService.store()` — embed memory content before insert
- `MemoryService.semantic_search()` — embed query, do cosine similarity via pgvector

---

## Background Jobs (Celery)

| Task | Trigger | Frequency |
|------|---------|-----------|
| `sync_gmail` | Scheduled cron | Every 5 min |
| `sync_outlook` | Scheduled cron | Every 5 min |
| `process_inbound_message` | On webhook receive | On demand |
| `generate_embeddings` | On memory create | On demand (async) |
| `generate_daily_briefing` | Scheduled cron | 6:00 AM daily |
| `cleanup_old_ai_logs` | Scheduled cron | Weekly |

---

## Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: realtyai
      POSTGRES_USER: realtyai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U realtyai"]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  backend:
    build: { context: ., dockerfile: docker/Dockerfile.backend }
    ports: ["8000:8000"]
    env_file: .env
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    volumes: ["./backend:/app"]
  
  worker:
    build: { context: ., dockerfile: docker/Dockerfile.worker }
    env_file: .env
    depends_on: [postgres, redis]
  
  frontend:
    build: { context: ./frontend, dockerfile: ../docker/Dockerfile.frontend }
    ports: ["3000:3000"]
    depends_on: [backend]

volumes:
  pgdata:
```

---

## Implementation Phases

### Phase 1: Foundation (Scaffold + Auth)
- Initialize new GitHub repo
- Docker Compose with postgres+pgvector, redis, backend containers
- Backend scaffold: FastAPI app, config, dependencies
- Database models (all tables) + Alembic init + first migration (pgvector extension)
- Auth service: JWT register/login/me
- Frontend scaffold: Next.js 15, shadcn/ui, Zustand auth store
- Login/signup pages + auth guard
- Health check endpoint

**Validation**: Docker compose up → register user → login → JWT stored → auth guard works

### Phase 2: CRM + Tasks
- Client service + API endpoints (CRUD)
- Task service + API endpoints (CRUD)
- Frontend: client list page, client detail page, client create/edit forms
- Frontend: task board page
- Async SQLAlchemy session management

**Validation**: CRUD clients, CRUD tasks, filter tasks by client/status

### Phase 3: DeepSeek Integration (AIService)
- `AIService` class with all methods
- Prompt templates (all 6 `.txt` files)
- Structured JSON output parsing with retry
- AI interaction logging
- Prompt testing: send known inputs, verify JSON output shape
- Tool definitions for Athena (10 tools)
- Athena chat endpoint: POST /chat

**Validation**: POST /chat "list my clients" → calls list_clients tool → returns formatted list

### Phase 4: Memory System (pgvector)
- Embedder service (fastembed + bge-small)
- Memory service: store, search, retrieve
- pgvector HNSW index
- Memory extraction: AIService.extract_memories() from messages
- Frontend: client memory browser on client detail page
- Semantic search endpoint

**Validation**: Store memory → embed created → semantic search returns relevant results

### Phase 5: Communication (Email)
- Integration service: OAuth connect for Gmail
- Communication service: inbound message processing
- Message pipeline (store → analyze → extract → create tasks → store memories)
- Celery worker: email sync task
- Frontend: messages page (inbound list)
- Frontend: integrations settings page

**Validation**: Connect Gmail → webhook fires → message stored → AI analysis runs → tasks created → memories extracted

### Phase 6: Daily Briefing
- Briefing service: gather tasks, messages, deadlines, memories
- AIService.generate_briefing() → structured briefing
- Celery scheduled task: generate daily at 6 AM
- Frontend: briefing page, dashboard briefing widget
- Briefing history storage + listing

**Validation**: Trigger briefing generation → structured output → dashboard shows priority tasks

### Phase 7: SMS + Polish
- Twilio integration (adapter pattern)
- SMS webhook handler
- SMS message pipeline (same as email)
- Frontend: SMS message display
- Athena tools: draft_reply, summarize_conversation
- Search page (keyword + semantic combined)
- Error states, loading skeletons, empty states on all pages

**Validation**: SMS webhook → pipeline runs → AI reply drafts → semantic search works

---

## Migration from Current System

What to copy:
- `packages/hermes/src/hermes/scraper/zillow.py` → copy into `backend/app/services/listing_service.py` (refactor inline)
- `packages/hermes/src/hermes/scraper/pipeline.py` → merge into `listing_service.py`
- Auth patterns from `apps/api/src/auth.py` → refactored into `auth_service.py`
- Athena system prompt → adapted into `prompts/athena_system.txt`

What to NOT copy:
- Mem0 / Qdrant / SQLite memory
- Multi-LLM fallback chains (resilient_llm, free_llm)
- CrewAI / multi-agent framework
- Monolithic main.py patterns
- Legacy hermes memory tables (athena_facts, athena_conv_threads, etc.)
- Marketing campaigns, calendar, documents, leads modules
- LangChain agent implementation (use direct OpenAI-compatible client for DeepSeek function calling)

How to port:
1. Copy Zillow scraper code into `backend/app/services/`
2. Rewrite `apps/api/src/auth.py` patterns into clean `auth_service.py` with proper DI
3. Start fresh database with Alembic migrations
4. Write new prompt templates optimized for DeepSeek Flash V4

---

## Risks

| Risk | Mitigation |
|------|-----------|
| DeepSeek Flash V4 JSON output inconsistency | Retry with error feedback, fallback to unstructured + regex parse |
| pgvector performance at scale | HNSW index from start, paginate search results |
| Email OAuth token refresh failures | Monitor token expiry, alert user to reconnect |
| Celery worker memory leak (fastembed model) | Separate worker pool for embedding tasks, restart policy |
| DeepSeek API rate limits | Exponential backoff, queue high-priority first |

## Open Questions

1. **GitHub repo name**: `realty-ai-v1`? `realty-assistant`?
2. **Deployment target**: VPS (185.80.130.197) or new platform?
3. **Telegram/Slack bots**: Port from current system or drop for V1?
4. **Multi-tenancy**: Brokerage/team structure deferred to Phase 2. Add `brokerage_id` FK to users table now?

---

## File Manifest (Files to Create)

Total: ~75 files

### Backend (~40 files)
- 15 model files
- 12 schema files
- 8 service files
- 6 prompt template files
- 9 API route files
- config.py, deps.py, main.py
- embedder.py
- celery_app.py, tasks.py

### Frontend (~25 files)
- 13 page files
- 8 component files
- 8 hook files
- 2 store files
- 7 type files
- lib/api.ts, lib/auth.ts, lib/utils.ts

### Infrastructure (~10 files)
- 3 Dockerfiles
- docker-compose.yml, docker-compose.prod.yml
- .env.example
- Makefile
- README.md
- alembic config + initial migration
