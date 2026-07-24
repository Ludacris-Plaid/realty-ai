"""
Athena Agent — Persistent Memory System (PostgreSQL).

Replaces the SQLite-backed memory with a unified PostgreSQL store.
Uses the same sync SQLAlchemy pattern as packages/ai/db.py.

Tables (all prefixed athena_*):
  athena_facts           — user facts / knowledge
  athena_conv_threads    — conversation threads
  athena_chat_messages   — individual chat messages
  athena_conversations   — summarised conversation records
  athena_skills          — learned skills
  athena_notes           — markdown notes
  athena_bot_configs     — bot integration tokens
"""
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Engine ──────────────────────────────────────────────────────────────────

_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://realty:realty_local_dev@localhost:5433/realty_ai",
).replace("+asyncpg", "").replace("+psycopg", "")

_engine = create_engine(_DB_URL, echo=False, pool_pre_ping=True)


def _ensure_tables():
    """Create athena_* tables if they don't exist. Called once on first use."""
    with _engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_facts (
                id          SERIAL PRIMARY KEY,
                category    TEXT NOT NULL DEFAULT 'general',
                key         TEXT NOT NULL UNIQUE,
                value       TEXT NOT NULL,
                confidence  FLOAT DEFAULT 1.0,
                source      TEXT DEFAULT 'inference',
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_conv_threads (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL DEFAULT '',
                title       TEXT DEFAULT '',
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_athena_conv_threads_user
                ON athena_conv_threads(user_id, is_active, created_at)
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_chat_messages (
                id              SERIAL PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES athena_conv_threads(id),
                role            TEXT NOT NULL CHECK (role IN ('user','assistant')),
                content         TEXT NOT NULL,
                tool_calls      TEXT DEFAULT '',
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_athena_conv_created
                ON athena_chat_messages(conversation_id, created_at)
        """))
        # Add user_id column to existing tables if missing (migration)
        for tbl in ["athena_conv_threads", "athena_facts", "athena_chat_messages", "athena_conversations", "athena_notes"]:
            try:
                conn.execute(text(f"""
                    DO $$ BEGIN
                        ALTER TABLE {tbl} ADD COLUMN user_id TEXT NOT NULL DEFAULT '';
                    EXCEPTION WHEN duplicate_column THEN NULL;
                    END $$;
                """))
            except Exception:
                pass  # Some dialects don't support IF NOT EXISTS — ignore
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_conversations (
                id           TEXT PRIMARY KEY,
                title        TEXT,
                summary      TEXT,
                user_goal    TEXT,
                agent_action TEXT,
                outcome      TEXT,
                created_at   TIMESTAMPTZ DEFAULT NOW(),
                updated_at   TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_skills (
                id            SERIAL PRIMARY KEY,
                name          TEXT UNIQUE NOT NULL,
                description   TEXT,
                trigger_phrase TEXT,
                steps         JSONB DEFAULT '[]',
                usage_count   INT DEFAULT 0,
                success_rate  FLOAT DEFAULT 1.0,
                created_at    TIMESTAMPTZ DEFAULT NOW(),
                updated_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_notes (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                body        TEXT NOT NULL,
                tags        JSONB DEFAULT '[]',
                source      TEXT DEFAULT 'agent',
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athena_bot_configs (
                id          SERIAL PRIMARY KEY,
                platform    TEXT UNIQUE NOT NULL,
                config_json JSONB DEFAULT '{}',
                enabled     BOOLEAN DEFAULT FALSE,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()


# Run table creation once at import time (non-fatal if DB unavailable)
try:
    _ensure_tables()
except Exception as _e:
    logger.warning(f"athena memory: could not ensure tables: {_e}")


# ─── User Facts ───────────────────────────────────────────────────────────────

def remember(key: str, value: str, category: str = "general",
             confidence: float = 1.0, source: str = "inference"):
    """Store a fact about the user. Upserts if key exists.
    
    Guards: empty key or value are silently rejected to avoid
    polluting the profile with junk entries.
    """
    if not key or not key.strip():
        logger.debug("remember() called with empty key — skipped")
        return
    if not value or not value.strip():
        logger.debug("remember() called with empty value — skipped")
        return
    key = key.strip()
    value = value.strip()
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_facts (category, key, value, confidence, source, updated_at)
            VALUES (:cat, :key, :val, :conf, :src, NOW())
            ON CONFLICT (key) DO UPDATE SET
                value      = EXCLUDED.value,
                confidence = GREATEST(athena_facts.confidence, EXCLUDED.confidence),
                updated_at = NOW(),
                source     = CASE WHEN EXCLUDED.source = 'explicit'
                                  THEN 'explicit' ELSE athena_facts.source END
        """), {"cat": category, "key": key, "val": value, "conf": confidence, "src": source})
        s.commit()


def forget(key: str):
    with Session(_engine) as s:
        s.execute(text("DELETE FROM athena_facts WHERE key = :key"), {"key": key})
        s.commit()


def get_user_profile() -> dict:
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT category, key, value, confidence
            FROM athena_facts ORDER BY category, confidence DESC
        """)).fetchall()
    profile: dict = {}
    for cat, key, val, conf in rows:
        profile.setdefault(cat, []).append({"key": key, "value": val, "confidence": conf})
    return profile


def profile_summary() -> str:
    profile = get_user_profile()
    if not profile:
        return "I'm still getting to know you."
    parts = []
    for cat, facts in profile.items():
        items = [f"  - {f['key']}: {f['value']}" for f in facts[:5]]
        parts.append(f"**{cat.title()}**:\n" + "\n".join(items))
    return "\n\n".join(parts)


def _search_facts(query: str, limit: int = 10) -> list[dict]:
    q = f"%{query}%"
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT key, value, category, confidence, source, updated_at
            FROM athena_facts
            WHERE key ILIKE :q OR value ILIKE :q OR category ILIKE :q
            ORDER BY confidence DESC, updated_at DESC
            LIMIT :lim
        """), {"q": q, "lim": limit}).fetchall()
    return [
        {"type": "fact", "key": r[0], "content": r[1], "category": r[2],
         "confidence": r[3], "source": r[4], "updated_at": str(r[5])}
        for r in rows
    ]


# ─── Conversation Threads & Messages ─────────────────────────────────────────

def get_or_create_active_conversation(user_id: str = "") -> str:
    with Session(_engine) as s:
        row = s.execute(text("""
            SELECT id FROM athena_conv_threads
            WHERE user_id = :uid AND is_active = TRUE
            ORDER BY created_at DESC LIMIT 1
        """), {"uid": user_id}).fetchone()
        if row:
            return row[0]
        conv_id = str(uuid.uuid4())
        s.execute(text("""
            INSERT INTO athena_conv_threads (id, user_id, title, is_active)
            VALUES (:id, :uid, 'Chat', TRUE)
        """), {"id": conv_id, "uid": user_id})
        s.commit()
        return conv_id


def save_message(conversation_id: str, role: str, content: str, tool_calls: str = ""):
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_chat_messages (conversation_id, role, content, tool_calls)
            VALUES (:cid, :role, :content, :tc)
        """), {"cid": conversation_id, "role": role, "content": content, "tc": tool_calls})
        s.commit()


def get_conversation_messages(conversation_id: str, limit: int = 200) -> list[dict]:
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT role, content, tool_calls, created_at
            FROM athena_chat_messages
            WHERE conversation_id = :cid
            ORDER BY created_at ASC
            LIMIT :lim
        """), {"cid": conversation_id, "lim": limit}).fetchall()
    return [
        {"role": r[0], "content": r[1], "tool_calls": r[2] or "",
         "timestamp": r[3].isoformat() if r[3] else ""}
        for r in rows
    ]


def list_conversations(user_id: str = "", limit: int = 50) -> list[dict]:
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT ct.id, ct.title, ct.is_active, ct.created_at,
                   COUNT(cm.id)  AS msg_count,
                   MAX(cm.content) FILTER (
                       WHERE cm.created_at = (
                           SELECT MAX(created_at) FROM athena_chat_messages
                           WHERE conversation_id = ct.id
                       )
                   ) AS last_msg
            FROM athena_conv_threads ct
            LEFT JOIN athena_chat_messages cm ON cm.conversation_id = ct.id
            WHERE ct.user_id = :uid
            GROUP BY ct.id, ct.title, ct.is_active, ct.created_at
            ORDER BY ct.created_at DESC
            LIMIT :lim
        """), {"uid": user_id, "lim": limit}).fetchall()
    return [
        {
            "id": r[0], "title": r[1], "is_active": bool(r[2]),
            "created_at": r[3].isoformat() if r[3] else "",
            "message_count": r[4] or 0,
            "last_message": (r[5] or "")[:120],
        }
        for r in rows
    ]


def update_conversation_title(conversation_id: str, title: str):
    with Session(_engine) as s:
        s.execute(text("""
            UPDATE athena_conv_threads
            SET title = :title, updated_at = NOW()
            WHERE id = :id
        """), {"title": title, "id": conversation_id})
        s.commit()


def reset_conversation(user_id: str = "") -> str:
    """Mark active conversation inactive and start a fresh one. Returns new ID."""
    conv_id = str(uuid.uuid4())
    with Session(_engine) as s:
        s.execute(text("""
            UPDATE athena_conv_threads SET is_active = FALSE
            WHERE user_id = :uid AND is_active = TRUE
        """), {"uid": user_id})
        s.execute(text("""
            INSERT INTO athena_conv_threads (id, user_id, title, is_active)
            VALUES (:id, :uid, 'Chat', TRUE)
        """), {"id": conv_id, "uid": user_id})
        s.commit()
    return conv_id


def _search_chat_messages(query: str, limit: int = 10) -> list[dict]:
    q = f"%{query}%"
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT cm.content, cm.role, cm.created_at, ct.title
            FROM athena_chat_messages cm
            JOIN athena_conv_threads ct ON cm.conversation_id = ct.id
            WHERE cm.content ILIKE :q
            ORDER BY cm.created_at DESC
            LIMIT :lim
        """), {"q": q, "lim": limit}).fetchall()
    return [
        {"type": "chat", "content": r[0][:300], "role": r[1],
         "created_at": r[2].isoformat() if r[2] else "", "conversation": r[3] or "Chat"}
        for r in rows
    ]


# ─── Summarised Conversations ─────────────────────────────────────────────────

def save_conversation(conv_id: str, title: str, summary: str, goal: str = "",
                      action: str = "", outcome: str = ""):
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_conversations
                (id, title, summary, user_goal, agent_action, outcome, updated_at)
            VALUES (:id, :title, :summary, :goal, :action, :outcome, NOW())
            ON CONFLICT (id) DO UPDATE SET
                title        = COALESCE(NULLIF(EXCLUDED.title, ''), athena_conversations.title),
                summary      = EXCLUDED.summary,
                user_goal    = EXCLUDED.user_goal,
                agent_action = EXCLUDED.agent_action,
                outcome      = EXCLUDED.outcome,
                updated_at   = NOW()
        """), {"id": conv_id, "title": title, "summary": summary,
               "goal": goal, "action": action, "outcome": outcome})
        s.commit()


def search_conversations(query: str, limit: int = 10) -> list[dict]:
    """Full-text search on past conversations using PostgreSQL tsvector."""
    q = f"%{query}%"
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT id, title, summary, created_at
            FROM athena_conversations
            WHERE title ILIKE :q OR summary ILIKE :q
               OR user_goal ILIKE :q OR agent_action ILIKE :q
            ORDER BY created_at DESC
            LIMIT :lim
        """), {"q": q, "lim": limit}).fetchall()
    return [
        {"id": r[0], "title": r[1], "summary": r[2],
         "created_at": r[3].isoformat() if r[3] else ""}
        for r in rows
    ]


# ─── Skills ───────────────────────────────────────────────────────────────────

def save_skill(name: str, description: str, trigger_phrase: str, steps: list[str]):
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_skills (name, description, trigger_phrase, steps)
            VALUES (:name, :desc, :trigger, :steps)
            ON CONFLICT (name) DO UPDATE SET
                description    = EXCLUDED.description,
                trigger_phrase = EXCLUDED.trigger_phrase,
                steps          = EXCLUDED.steps,
                updated_at     = NOW()
        """), {"name": name, "desc": description, "trigger": trigger_phrase,
               "steps": json.dumps(steps)})
        s.commit()


def get_skills() -> list[dict]:
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT name, description, trigger_phrase, usage_count, success_rate
            FROM athena_skills ORDER BY usage_count DESC
        """)).fetchall()
    return [
        {"name": r[0], "description": r[1], "trigger": r[2],
         "uses": r[3], "success_rate": r[4]}
        for r in rows
    ]


# ─── Notes ────────────────────────────────────────────────────────────────────

def save_note(title: str, body: str, tags: list[str] = None, source: str = "agent") -> str:
    tags = tags or []
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_notes (title, body, tags, source)
            VALUES (:title, :body, :tags, :source)
        """), {"title": title, "body": body, "tags": json.dumps(tags), "source": source})
        s.commit()
    return title


def search_notes(query: str) -> list[dict]:
    q = f"%{query}%"
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT title, body, tags, source, created_at
            FROM athena_notes
            WHERE title ILIKE :q OR body ILIKE :q
            ORDER BY created_at DESC LIMIT 20
        """), {"q": q}).fetchall()
    return [
        {"title": r[0], "body": r[1][:200], "tags": r[2] or [],
         "source": r[3], "created": r[4].isoformat() if r[4] else ""}
        for r in rows
    ]


def _search_notes(query: str, limit: int = 10) -> list[dict]:
    q = f"%{query}%"
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT title, body, tags, source, created_at
            FROM athena_notes
            WHERE title ILIKE :q OR body ILIKE :q
            ORDER BY created_at DESC LIMIT :lim
        """), {"q": q, "lim": limit}).fetchall()
    return [
        {"type": "note", "key": r[0], "content": r[1][:300],
         "tags": r[2] or [], "source": r[3],
         "created_at": r[4].isoformat() if r[4] else ""}
        for r in rows
    ]


# ─── Bot Configs ──────────────────────────────────────────────────────────────

def get_bot_config(platform: str) -> dict:
    with Session(_engine) as s:
        row = s.execute(text("""
            SELECT config_json, enabled FROM athena_bot_configs
            WHERE platform = :platform
        """), {"platform": platform}).fetchone()
    if not row:
        return {"enabled": False, "config": {}}
    cfg = row[0] if isinstance(row[0], dict) else json.loads(row[0] or "{}")
    return {"enabled": bool(row[1]), "config": cfg}


def save_bot_config(platform: str, config: dict, enabled: bool = False):
    with Session(_engine) as s:
        s.execute(text("""
            INSERT INTO athena_bot_configs (platform, config_json, enabled, updated_at)
            VALUES (:platform, :config, :enabled, NOW())
            ON CONFLICT (platform) DO UPDATE SET
                config_json = EXCLUDED.config_json,
                enabled     = EXCLUDED.enabled,
                updated_at  = NOW()
        """), {"platform": platform, "config": json.dumps(config),
               "enabled": enabled})
        s.commit()


def delete_bot_config(platform: str):
    with Session(_engine) as s:
        s.execute(text("DELETE FROM athena_bot_configs WHERE platform = :p"),
                  {"p": platform})
        s.commit()


def list_bot_configs() -> dict:
    with Session(_engine) as s:
        rows = s.execute(text("""
            SELECT platform, config_json, enabled, updated_at
            FROM athena_bot_configs
        """)).fetchall()
    result = {}
    for r in rows:
        cfg = r[1] if isinstance(r[1], dict) else json.loads(r[1] or "{}")
        result[r[0]] = {
            "platform": r[0], "config": cfg,
            "enabled": bool(r[2]),
            "updated_at": r[3].isoformat() if r[3] else "",
        }
    return result


# ─── Multi-source recall ──────────────────────────────────────────────────────

def recall(query: str, top_k: int = 10) -> list[dict]:
    """Multi-source search: facts + conversations + chat messages + notes."""
    conv_results = search_conversations(query, limit=5)
    conv_formatted = [
        {"type": "conversation", "key": c.get("title", ""),
         "content": c.get("summary", ""), "created_at": c.get("created_at", "")}
        for c in conv_results
    ]
    fact_results  = _search_facts(query, top_k)
    chat_results  = _search_chat_messages(query, 5)
    note_results  = _search_notes(query, 5)

    seen: set = set()
    merged = []
    for item in conv_formatted + fact_results + chat_results + note_results:
        key = item.get("content", "")[:100].lower()
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    return merged[:top_k]


# ─── Consolidation ────────────────────────────────────────────────────────────

def cleanup_empty_facts() -> int:
    """Remove facts with empty keys or values. Returns count removed."""
    with Session(_engine) as s:
        result = s.execute(
            text("DELETE FROM athena_facts WHERE key = '' OR key IS NULL OR value = '' OR value IS NULL")
        )
        s.commit()
    count = result.rowcount if result else 0
    if count > 0:
        logger.info(f"Cleaned up {count} empty fact(s) from memory profile")
    return count


# Clean up any empty facts on import (from stale interactions)
try:
    cleanup_empty_facts()
except Exception:
    pass


def consolidate() -> dict:
    """Surface patterns from recent conversations. Called periodically."""
    with Session(_engine) as s:
        topics = s.execute(text("""
            SELECT user_goal, COUNT(*) AS cnt
            FROM athena_conversations
            WHERE user_goal != '' AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY user_goal ORDER BY cnt DESC LIMIT 10
        """)).fetchall()
        fact_count = s.execute(
            text("SELECT COUNT(*) FROM athena_facts")
        ).scalar() or 0
    return {
        "total_facts": fact_count,
        "top_topics": [{"topic": t[0], "count": t[1]} for t in topics],
    }
