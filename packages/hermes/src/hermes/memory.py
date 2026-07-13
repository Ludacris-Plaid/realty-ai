"""
Athena Agent — Persistent Memory System.

Functions like a personal notebook for your digital secretary.
- Stores user facts (preferences, style, clients, history)
- FTS5 full-text search on past conversations
- Periodic memory consolidation
- User profile grows across sessions
"""
import json
import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "athena")
os.makedirs(MEMORY_DIR, exist_ok=True)
DB_PATH = os.path.join(MEMORY_DIR, "athena_memory.db")
NOTES_DIR = os.path.join(MEMORY_DIR, "notes")
os.makedirs(NOTES_DIR, exist_ok=True)


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL DEFAULT 'general',
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'inference',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_key ON user_facts(key);
        
        CREATE TABLE IF NOT EXISTS conversation_threads (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL,
            tool_calls TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversation_threads(id)
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON chat_messages(conversation_id, created_at);
        
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            user_goal TEXT,
            agent_action TEXT,
            outcome TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE VIRTUAL TABLE IF NOT EXISTS conversation_fts USING fts5(
            title, summary, user_goal, agent_action, outcome,
            content='conversations', content_rowid='rowid'
        );
        
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            trigger_phrase TEXT,
            steps TEXT,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            source TEXT DEFAULT 'agent',
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS bot_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL UNIQUE,
            config_json TEXT NOT NULL DEFAULT '{}',
            enabled INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ─── User Facts (grows knowledge about user) ──────────────────────────────

def remember(key: str, value: str, category: str = "general", confidence: float = 1.0, source: str = "inference"):
    """Store a fact about the user. Upserts if key exists."""
    conn = _get_db()
    conn.execute("""
        INSERT INTO user_facts (category, key, value, confidence, source, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            confidence = MAX(user_facts.confidence, excluded.confidence),
            updated_at = excluded.updated_at,
            source = CASE WHEN excluded.source = 'explicit' THEN 'explicit' ELSE user_facts.source END
    """, (category, key, value, confidence, source))
    conn.commit()
    conn.close()


def _search_facts(query: str, limit: int = 10) -> list[dict]:
    """Search user facts table by substring match on key/value/category."""
    conn = _get_db()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT key, value, category, confidence, source, updated_at
        FROM user_facts
        WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
        ORDER BY confidence DESC, updated_at DESC
        LIMIT ?
    """, (q, q, q, limit)).fetchall()
    conn.close()
    return [
        {"type": "fact", "key": r[0], "content": r[1], "category": r[2],
         "confidence": r[3], "source": r[4], "updated_at": r[5]}
        for r in rows
    ]


def _search_chat_messages(query: str, limit: int = 10) -> list[dict]:
    """Search chat message content."""
    conn = _get_db()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT cm.content, cm.role, cm.created_at, ct.title
        FROM chat_messages cm
        JOIN conversation_threads ct ON cm.conversation_id = ct.id
        WHERE cm.content LIKE ?
        ORDER BY cm.created_at DESC
        LIMIT ?
    """, (q, limit)).fetchall()
    conn.close()
    return [
        {"type": "chat", "content": r[0][:300], "role": r[1],
         "created_at": r[2], "conversation": r[3] or "Chat"}
        for r in rows
    ]


def _search_notes(query: str, limit: int = 10) -> list[dict]:
    """Search notes by title or body."""
    conn = _get_db()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT title, body, tags, source, created_at
        FROM notes WHERE title LIKE ? OR body LIKE ?
        ORDER BY created_at DESC LIMIT ?
    """, (q, q, limit)).fetchall()
    conn.close()
    return [
        {"type": "note", "key": r[0], "content": r[1][:300], "tags": json.loads(r[2]) if r[2] else [],
         "source": r[3], "created_at": r[4]}
        for r in rows
    ]


def recall(query: str, top_k: int = 10) -> list[dict]:
    """Multi-source search across facts, conversations, chat messages, and notes.
    
    Combines results from all sources, deduplicates by content,
    and returns the most relevant entries ranked by source priority.
    """
    # FTS5 on conversations (best match)
    conv_results = search_conversations(query, limit=5)
    conv_formatted = [
        {"type": "conversation", "key": c.get("title", ""), "content": c.get("summary", ""),
         "created_at": c.get("created_at", "")}
        for c in conv_results
    ]
    
    # LIke search on facts, chat messages, notes
    fact_results = _search_facts(query, top_k)
    chat_results = _search_chat_messages(query, 5)
    note_results = _search_notes(query, 5)
    
    # Merge all results, deduplicate by content
    seen = set()
    merged = []
    for item in conv_formatted + fact_results + chat_results + note_results:
        content_key = item.get("content", "")[:100].lower()
        if content_key and content_key not in seen:
            seen.add(content_key)
            merged.append(item)
    
    return merged[:top_k]


def forget(key: str):
    conn = _get_db()
    conn.execute("DELETE FROM user_facts WHERE key = ?", (key,))
    conn.commit()
    conn.close()


def get_user_profile() -> dict:
    """Get the full user profile as a formatted string."""
    conn = _get_db()
    rows = conn.execute("""
        SELECT category, key, value, confidence FROM user_facts
        ORDER BY category, confidence DESC
    """).fetchall()
    conn.close()
    profile = {}
    for cat, key, val, conf in rows:
        if cat not in profile:
            profile[cat] = []
        profile[cat].append({"key": key, "value": val, "confidence": conf})
    return profile


def profile_summary() -> str:
    """Get a text summary of what the agent knows about the user."""
    profile = get_user_profile()
    if not profile:
        return "I'm still getting to know you."
    parts = []
    for cat, facts in profile.items():
        items = [f"  - {f['key']}: {f['value']}" for f in facts[:5]]
        parts.append(f"**{cat.title()}**:\n" + "\n".join(items))
    return "\n\n".join(parts)


# ─── Conversation Memory ──────────────────────────────────────────────────

def save_conversation(conv_id: str, title: str, summary: str, goal: str = "",
                       action: str = "", outcome: str = ""):
    conn = _get_db()
    conn.execute("""
        INSERT INTO conversations (id, title, summary, user_goal, agent_action, outcome, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            title = COALESCE(NULLIF(excluded.title, ''), conversations.title),
            summary = excluded.summary,
            user_goal = excluded.user_goal,
            agent_action = excluded.agent_action,
            outcome = excluded.outcome,
            updated_at = excluded.updated_at
    """, (conv_id, title, summary, goal, action, outcome))
    # Also update FTS index
    conn.execute("""
        INSERT INTO conversation_fts (rowid, title, summary, user_goal, agent_action, outcome)
        VALUES (last_insert_rowid(), ?, ?, ?, ?, ?)
    """, (title, summary, goal, action, outcome))
    conn.commit()
    conn.close()


def search_conversations(query: str, limit: int = 10) -> list[dict]:
    """FTS5 full-text search on past conversations."""
    conn = _get_db()
    try:
        rows = conn.execute("""
            SELECT c.id, c.title, c.summary, c.created_at,
                   rank FROM conversation_fts
            WHERE conversation_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return [
        {"id": r[0], "title": r[1], "summary": r[2], "created_at": r[3]}
        for r in rows
    ]


# ─── Skills Memory ────────────────────────────────────────────────────────

def save_skill(name: str, description: str, trigger_phrase: str, steps: list[str]):
    conn = _get_db()
    conn.execute("""
        INSERT INTO skills (name, description, trigger_phrase, steps)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            trigger_phrase = excluded.trigger_phrase,
            steps = excluded.steps,
            updated_at = datetime('now')
    """, (name, description, trigger_phrase, json.dumps(steps)))
    conn.commit()
    conn.close()


def get_skills() -> list[dict]:
    conn = _get_db()
    rows = conn.execute("""
        SELECT name, description, trigger_phrase, usage_count, success_rate
        FROM skills ORDER BY usage_count DESC
    """).fetchall()
    conn.close()
    return [
        {"name": r[0], "description": r[1], "trigger": r[2],
         "uses": r[3], "success_rate": r[4]}
        for r in rows
    ]


# ─── Notes (Obsidian-style) ───────────────────────────────────────────────

def save_note(title: str, body: str, tags: list[str] = None, source: str = "agent"):
    """Save a markdown note file (Obsidian-compatible)."""
    tags = tags or []
    safe_title = title.replace("/", "-").replace(" ", "-")
    path = os.path.join(NOTES_DIR, f"{safe_title}.md")
    
    with open(path, "w") as f:
        f.write(f"---\ntitle: {title}\ntags: {json.dumps(tags)}\nsource: {source}\ndate: {datetime.now().isoformat()}\n---\n\n{body}\n")
    
    # Also store in DB
    conn = _get_db()
    conn.execute("""
        INSERT INTO notes (title, body, tags, source)
        VALUES (?, ?, ?, ?)
    """, (title, body, json.dumps(tags), source))
    conn.commit()
    conn.close()
    return path


def search_notes(query: str) -> list[dict]:
    conn = _get_db()
    q = f"%{query}%"
    rows = conn.execute("""
        SELECT title, body, tags, source, created_at
        FROM notes WHERE title LIKE ? OR body LIKE ?
        ORDER BY created_at DESC LIMIT 20
    """, (q, q)).fetchall()
    conn.close()
    return [
        {"title": r[0], "body": r[1][:200], "tags": json.loads(r[2]), "source": r[3], "created": r[4]}
        for r in rows
    ]


# ─── Memory Nudge (periodic consolidation) ────────────────────────────────

def consolidate():
    """Called periodically by the agent to consolidate and surface insights."""
    conn = _get_db()
    
    # Find patterns: repeated topics in conversations
    topics = conn.execute("""
        SELECT user_goal, COUNT(*) as cnt FROM conversations
        WHERE user_goal != '' AND created_at > datetime('now', '-30 days')
        GROUP BY user_goal ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    
    # Check for user facts gaps
    fact_count = conn.execute("SELECT COUNT(*) FROM user_facts").fetchone()[0]
    
    conn.close()
    
    return {
        "total_facts": fact_count,
        "top_topics": [{"topic": t[0], "count": t[1]} for t in topics],
    }


# ─── Persistent Conversation Threads ──────────────────────────────────────

def get_or_create_active_conversation() -> str:
    """Get the active conversation ID, or create one if none exists."""
    conn = _get_db()
    row = conn.execute(
        "SELECT id FROM conversation_threads WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if row:
        conn.close()
        return row[0]
    # Create a new conversation
    import uuid
    conv_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO conversation_threads (id, title, is_active) VALUES (?, ?, 1)",
        (conv_id, "Chat")
    )
    conn.commit()
    conn.close()
    return conv_id


def save_message(conversation_id: str, role: str, content: str, tool_calls: str = ""):
    """Save a single chat message to the conversation thread."""
    conn = _get_db()
    conn.execute(
        "INSERT INTO chat_messages (conversation_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, tool_calls)
    )
    conn.commit()
    conn.close()


def get_conversation_messages(conversation_id: str, limit: int = 200) -> list[dict]:
    """Get all messages for a conversation, ordered by time."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT role, content, tool_calls, created_at FROM chat_messages "
        "WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
        (conversation_id, limit)
    ).fetchall()
    conn.close()
    return [
        {"role": r[0], "content": r[1], "tool_calls": r[2], "timestamp": r[3]}
        for r in rows
    ]


def list_conversations(limit: int = 50) -> list[dict]:
    """List all conversation threads, newest first."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT ct.id, ct.title, ct.is_active, ct.created_at, "
        "  (SELECT COUNT(*) FROM chat_messages WHERE conversation_id = ct.id) as msg_count, "
        "  (SELECT content FROM chat_messages WHERE conversation_id = ct.id ORDER BY created_at DESC LIMIT 1) as last_msg "
        "FROM conversation_threads ct ORDER BY ct.created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0], "title": r[1], "is_active": bool(r[2]),
            "created_at": r[3], "message_count": r[4],
            "last_message": (r[5] or "")[:120]
        }
        for r in rows
    ]


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation thread."""
    conn = _get_db()
    conn.execute(
        "UPDATE conversation_threads SET title = ?, updated_at = datetime('now') WHERE id = ?",
        (title, conversation_id)
    )
    conn.commit()
    conn.close()


def reset_conversation() -> str:
    """Mark active conversation inactive and create a fresh one. Returns new ID."""
    conn = _get_db()
    conn.execute("UPDATE conversation_threads SET is_active = 0 WHERE is_active = 1")
    import uuid
    conv_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO conversation_threads (id, title, is_active) VALUES (?, ?, 1)",
        (conv_id, "Chat")
    )
    conn.commit()
    conn.close()
    return conv_id


# ─── Bot Configurations (Telegram, Slack) ──────────────────────────────────

def get_bot_config(platform: str) -> dict:
    """Get bot configuration for a platform. Returns empty dict if not set."""
    conn = _get_db()
    row = conn.execute(
        "SELECT config_json, enabled FROM bot_configs WHERE platform = ?",
        (platform,)
    ).fetchone()
    conn.close()
    if not row:
        return {"enabled": False, "config": {}}
    return {"enabled": bool(row[1]), "config": json.loads(row[0])}


def save_bot_config(platform: str, config: dict, enabled: bool = False):
    """Save bot configuration for a platform. Upserts if exists."""
    conn = _get_db()
    conn.execute("""
        INSERT INTO bot_configs (platform, config_json, enabled, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(platform) DO UPDATE SET
            config_json = excluded.config_json,
            enabled = excluded.enabled,
            updated_at = excluded.updated_at
    """, (platform, json.dumps(config), 1 if enabled else 0))
    conn.commit()
    conn.close()


def delete_bot_config(platform: str):
    """Remove bot configuration for a platform."""
    conn = _get_db()
    conn.execute("DELETE FROM bot_configs WHERE platform = ?", (platform,))
    conn.commit()
    conn.close()


def list_bot_configs() -> dict:
    """Get all bot configurations."""
    conn = _get_db()
    rows = conn.execute(
        "SELECT platform, config_json, enabled, updated_at FROM bot_configs"
    ).fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r[0]] = {
            "platform": r[0],
            "config": json.loads(r[1]),
            "enabled": bool(r[2]),
            "updated_at": r[3],
        }
    return result
