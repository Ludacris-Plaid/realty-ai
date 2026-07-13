# RealtyAI — AI Operating System for Real Estate Agents

RealtyAI is a full-stack AI platform that helps real estate agents manage leads, automate follow-ups, generate marketing content, and stay organized.

## Stack

- **Frontend:** Next.js 15 + Tailwind + shadcn/ui
- **Backend:** Python FastAPI + SQLAlchemy + Alembic
- **AI Layer:** LangGraph + LiteLLM + MCP
- **Database:** PostgreSQL + pgvector
- **Queue:** Redis
- **Local AI:** llama.cpp (localhost:8000)

## Quick Start

```bash
# Start everything
docker compose up -d

# Or run locally:
cd apps/api && pip install -e . && uvicorn src.main:app --reload
cd apps/web && npm install && npm run dev
```

## Structure

```
apps/
  web/       — Next.js customer dashboard
  api/       — FastAPI REST API
  worker/    — Background AI job processor
packages/
  ai/        — LangGraph agents, tools, MCP
  database/  — SQLAlchemy models + Alembic migrations
  mcp/       — Model Context Protocol servers
  workflows/ — Business process orchestration
  shared/    — Shared types (TypeScript)
```

## First Agent

The Realty Assistant Agent handles natural language requests:
- "Show me my hottest leads"
- "Write a follow-up email for John who viewed 123 Main St"
- "Summarize my active listings"
- "Who needs a call today?"
