"""
Mem0 Memory Adapter for Athena.

Provides automatic entity extraction, semantic search, and memory scoring
on top of the PostgreSQL-backed memory system.

Architecture:
  ┌─────────────┐     ┌──────────┐     ┌───────────┐
  │  Agent      │────▶│  MEM0    │────▶│  Qdrant   │
  │  (agent.py) │     │ Adapter  │     │ (vectors) │
  └─────────────┘     │          │     └───────────┘
        │             │          │     ┌───────────┐
        ▼             │          │────▶│ mem0_hist │
  ┌─────────────┐     │          │     │ (SQLite)  │
  │ PostgreSQL  │     └──────────┘     └───────────┘
  │ (facts,     │
  │  convos,    │
  │  notes,     │
  │  configs)   │
  └─────────────┘

Mem0 handles:
  - Automatic entity/fact extraction from conversation text
  - Semantic memory search ("what did we discuss about Windermere?")
  - Memory importance scoring with decay
  - Cross-user isolation (for future multi-agent support)
"""
import os
import json
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Directory for Mem0 data
MEM0_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "athena")
os.makedirs(MEM0_DIR, exist_ok=True)

# Default user ID (single-user mode, becomes multi-user with auth)
DEFAULT_USER_ID = "athena-user"


def _build_embedder_config():
    """Build embedder config from env vars.
    
    Provider options (MEM0_EMBEDDER_PROVIDER):
      - huggingface (default): uses local sentence-transformers (all-MiniLM-L6-v2).
        Fast, free, no API key needed. ~80MB model download on first use.
      - openai: reads OPENAI_API_KEY + OPENAI_BASE_URL
      - ollama: uses local Ollama instance
    
    Falls back to huggingface if available, otherwise openai.
    """
    from mem0.embeddings.configs import EmbedderConfig
    
    # Probe: check which providers are actually available
    _hf_available = None
    def _huggingface_available():
        nonlocal _hf_available
        if _hf_available is None:
            try:
                import sentence_transformers  # noqa: F401
                _hf_available = True
            except ImportError:
                _hf_available = False
        return _hf_available
    
    provider = os.environ.get("MEM0_EMBEDDER_PROVIDER", "").lower()
    
    # Auto-detect: prefer huggingface if installed, fallback to openai
    if not provider:
        provider = "huggingface" if _huggingface_available() else "openai"
    
    config = {"model": os.environ.get("MEM0_EMBEDDER_MODEL", "text-embedding-3-small")}
    dims = 1536
    
    if provider == "ollama":
        config["model"] = os.environ.get("MEM0_EMBEDDER_MODEL", "nomic-embed-text")
        config["embedding_dims"] = int(os.environ.get("MEM0_EMBEDDER_DIMS", "768"))
        dims = int(os.environ.get("MEM0_EMBEDDER_DIMS", "768"))
    elif provider == "huggingface":
        config["model"] = os.environ.get("MEM0_EMBEDDER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        dims = int(os.environ.get("MEM0_EMBEDDER_DIMS", "384"))  # all-MiniLM-L6-v2 → 384d
    
    return EmbedderConfig(provider=provider, config=config), dims


def _build_llm_config():
    """Build LLM config for Mem0 entity extraction.
    
    Provider options (MEM0_LLM_PROVIDER):
      - openai (default): reads OPENAI_API_KEY + OPENAI_BASE_URL
      - ollama: uses local Ollama
    """
    from mem0.llms.configs import LlmConfig
    provider = os.environ.get("MEM0_LLM_PROVIDER", "openai").lower()
    model = os.environ.get("MEM0_LLM_MODEL", "gpt-4o-mini" if provider == "openai" else "llama3.2")
    return LlmConfig(provider=provider, config={"model": model, "temperature": 0.1})


def _create_mem0_instance():
    """Create a configured Mem0 instance. Mem0 uses Qdrant for vectors + SQLite for history.
    
    Embedder config: env MEM0_EMBEDDER_PROVIDER (ollama|openai|huggingface), default ollama.
    LLM config: env MEM0_LLM_PROVIDER (openai|ollama), default openai (reads OPENAI_* env vars).
    
    Both fall through gracefully — init failure → SQLite fallback.
    """
    try:
        from mem0 import Memory
        from mem0.configs.base import MemoryConfig
        from mem0.vector_stores.configs import VectorStoreConfig
        from mem0.embeddings.configs import EmbedderConfig
        from mem0.llms.configs import LlmConfig
        import signal

        # Signal-based timeout guard — Mem0 init can hang if there are connectivity issues
        class TimeoutError(Exception): pass
        def _handler(signum, frame): raise TimeoutError("Mem0 init timed out")
        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(12)  # 12-second timeout (generous for ollama model pull)

        try:
            embedder, dims = _build_embedder_config()
            llm = _build_llm_config()
            
            embed_provider = embedder.provider
            embed_model = embedder.config.get("model", "unknown")
            
            config = MemoryConfig(
                vector_store=VectorStoreConfig(
                    provider="qdrant",
                    config={
                        "path": os.path.join(MEM0_DIR, "qdrant"),
                        "collection_name": "athena_memories",
                        "embedding_model_dims": dims,
                        "on_disk": True,
                    },
                ),
                embedder=embedder,
                llm=llm,
                history_db_path=os.path.join(MEM0_DIR, "mem0_history.db"),
                version="v1.1",
            )
            instance = Memory(config=config)
            signal.alarm(0)
            logger.info(f"Mem0 initialized (embedder={embed_provider}/{embed_model}, llm_provider={llm.provider}, dims={dims})")
            return instance
        except TimeoutError:
            signal.alarm(0)
            logger.warning("Mem0 init timed out. Running without semantic memory.")
            return None
        except Exception as e:
            signal.alarm(0)
            logger.warning(f"Mem0 init failed: {e}. Running without semantic memory.")
            return None
    except ImportError as e:
        logger.warning(f"Mem0 package not installed: {e}. Running without semantic memory.")
        return None


# ─── Singleton ──────────────────────────────────────────────────────────────

_instance = None

def _get_mem0():
    """Get or create the Mem0 singleton."""
    global _instance
    if _instance is None:
        _instance = _create_mem0_instance()
    return _instance


# ─── Public API ─────────────────────────────────────────────────────────────

def is_available() -> bool:
    """Check if Mem0 is properly initialized."""
    return _get_mem0() is not None


def add_interaction(user_message: str, assistant_response: str, user_id: str = DEFAULT_USER_ID,
                    metadata: dict = None) -> bool:
    """Feed a conversation turn to Mem0 for automatic memory extraction.

    Mem0's `add()` method receives messages in OpenAI chat format and
    automatically extracts entities, facts, preferences, and relationships.
    It handles deduplication, importance scoring, and storage internally.
    """
    mem0 = _get_mem0()
    if not mem0:
        return False

    try:
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response},
        ]
        mem0.add(
            messages,
            user_id=user_id,
            metadata=metadata or {"source": "chat"},
            infer=True,  # Auto-extract entities and relationships
        )
        return True
    except Exception as e:
        logger.warning(f"Mem0 add_interaction error: {e}")
        return False


def search_memories(query: str, user_id: str = DEFAULT_USER_ID, limit: int = 10) -> list[dict]:
    """Semantic search across all stored memories for a user.

    Returns memories ranked by relevance to the query.
    Each memory has: id, text, metadata, created_at, importance.
    """
    mem0 = _get_mem0()
    if not mem0:
        return []

    try:
        results = mem0.search(query, filters={"user_id": user_id}, top_k=limit)
        return _normalize_results(results)
    except Exception as e:
        logger.warning(f"Mem0 search error: {e}")
        return []


def get_all_memories(user_id: str = DEFAULT_USER_ID, limit: int = 50) -> list[dict]:
    """List all stored memories for a user."""
    mem0 = _get_mem0()
    if not mem0:
        return []

    try:
        results = mem0.get_all(filters={"user_id": user_id}, top_k=limit)
        return _normalize_results(results)
    except Exception as e:
        logger.warning(f"Mem0 get_all error: {e}")
        return []


def delete_memory(memory_id: str) -> bool:
    """Delete a single memory by its ID."""
    mem0 = _get_mem0()
    if not mem0:
        return False

    try:
        mem0.delete(memory_id)
        return True
    except Exception as e:
        logger.warning(f"Mem0 delete error: {e}")
        return False


def get_relevant_context(user_id: str = DEFAULT_USER_ID, limit: int = 5) -> str:
    """Get a formatted string of relevant memories for system prompt injection.

    Returns an empty string if no memories exist or Mem0 is unavailable.
    """
    mem0 = _get_mem0()
    if not mem0:
        return ""

    try:
        # Get most recent/important memories
        results = mem0.get_all(filters={"user_id": user_id}, top_k=limit)
        memories = _normalize_results(results)
        if not memories:
            return ""

        lines = ["**What I know about you:**"]
        for m in memories[:limit]:
            text = m.get("text", "")
            if text:
                # Truncate very long memories
                if len(text) > 200:
                    text = text[:197] + "..."
                lines.append(f"  • {text}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Mem0 get_relevant_context error: {e}")
        return ""


def get_user_memory_count(user_id: str = DEFAULT_USER_ID) -> int:
    """Get the count of stored memories for a user."""
    memories = get_all_memories(user_id, limit=1000)
    return len(memories)


# ─── Internal helpers ───────────────────────────────────────────────────────

def _normalize_results(results) -> list[dict]:
    """Normalize Mem0's response format into a consistent list of dicts."""
    if not results:
        return []

    # Mem0 returns results from search() as a list of dicts with 'memory' key
    # and from get_all() as a dict with 'results' key
    if isinstance(results, dict):
        results = results.get("results", [])

    normalized = []
    for r in results:
        if isinstance(r, str):
            normalized.append({"id": "", "text": r, "metadata": {}, "created_at": ""})
        elif isinstance(r, dict):
            normalized.append({
                "id": r.get("id", ""),
                "text": r.get("memory", r.get("text", "")),
                "metadata": r.get("metadata", {}),
                "created_at": r.get("created_at", r.get("timestamp", "")),
                "importance": r.get("importance", r.get("score", None)),
                "categories": r.get("categories", []),
            })
    return normalized


# ─── Migration from SQLite user_facts ──────────────────────────────────────

def migrate_from_sqlite(sqlite_memory_module) -> dict:
    """One-time migration: import existing SQLite user_facts into Mem0.

    Call this once after Mem0 is set up. It reads all facts from the
    existing user_facts table and adds them to Mem0 with explicit metadata.
    """
    if not is_available():
        return {"status": "skipped", "reason": "Mem0 not available", "count": 0}

    try:
        profile = sqlite_memory_module.get_user_profile()
        if not profile:
            return {"status": "noop", "count": 0}

        count = 0
        for category, facts in profile.items():
            for fact in facts:
                memory_text = f"[{category}] {fact['key']}: {fact['value']}"
                metadata = {
                    "source": "migration",
                    "category": category,
                    "original_key": fact["key"],
                    "confidence": fact["confidence"],
                }
                mem0 = _get_mem0()
                if mem0:
                    mem0.add(
                        memory_text,
                        user_id=DEFAULT_USER_ID,
                        metadata=metadata,
                        infer=False,
                    )
                    count += 1

        logger.info(f"Migrated {count} facts from SQLite to Mem0")
        return {"status": "success", "count": count}
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {"status": "error", "reason": str(e), "count": 0}
