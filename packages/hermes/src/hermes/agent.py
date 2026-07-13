"""
Athena Agent — Digital Secretary.

Your personal AI secretary. Warm, professional, intuitive.
Learns your style, remembers everything, grows with you.
Controls the entire RealtyAI system through natural conversation.
Handles leads, listings, documents, calendar, marketing, and more.
Knowledgeable in Canadian and US real estate law and practice.

Architecture: LangChain tool-calling agent with persistent memory.
"""
import os
import json
import logging
import uuid
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .memory import profile_summary as sqlite_profile_summary, remember, recall, save_conversation, search_conversations, consolidate as consolidate_memory, get_or_create_active_conversation, save_message, get_conversation_messages, reset_conversation as reset_conversation_db, list_conversations
from .mem0_adapter import (
    is_available as mem0_available,
    add_interaction as mem0_add_interaction,
    search_memories as mem0_search,
    get_all_memories as mem0_get_all,
    get_relevant_context as mem0_get_context,
    get_user_memory_count as mem0_memory_count,
    migrate_from_sqlite,
)
from .tools import TOOL_DEFINITIONS, execute_tool, set_engine

logger = logging.getLogger(__name__)

# ─── Convert tool definitions to LangChain tools ────────────────────────────

_built_tools = []

def _make_tool_func(tool_name: str, tool_desc: str):
    """Create a tool with name set before LangChain's @tool decorator reads it."""
    func = lambda **kwargs: execute_tool(tool_name, kwargs)
    func.__name__ = tool_name
    func.__doc__ = tool_desc
    return tool(func)

def _build_tools():
    """Create LangChain Tool objects from tool definitions."""
    global _built_tools
    if _built_tools:
        return _built_tools
    
    for td in TOOL_DEFINITIONS:
        _built_tools.append(_make_tool_func(td["name"], td["description"]))
    
    return _built_tools


# ─── Response sanitization ────────────────────────────────────────────────

import re

def _sanitize_response(text: str) -> str:
    """Strip tool-call XML artifacts from model responses.
    
    Some models (notably hy3-free) emit raw XML-like tool call syntax
    in the response text. Strip these before returning to the frontend.
    """
    if not text:
        return text
    
    # Strip <tool_calls:...>...</tool_calls:...> blocks
    text = re.sub(r'<tool_calls?:\w+>[^<]*</tool_calls?:\w+>', '', text)
    
    # Strip <tool_call:...>...</tool_call:...> blocks
    text = re.sub(r'<tool_call[^>]*>.*?</tool_call>', '', text, flags=re.DOTALL)
    
    # Strip <function_calls>...</function_calls> blocks
    text = re.sub(r'<function_calls>.*?</function_calls>', '', text, flags=re.DOTALL)
    
    # Strip <invoke>...</invoke> blocks (common XML tool format)
    text = re.sub(r'<invoke>.*?</invoke>', '', text, flags=re.DOTALL)
    
    # Strip function_call JSON blocks: {"name": "...", "arguments": {...}}
    text = re.sub(r'\{"name":\s*"[^"]*",\s*"arguments":\s*\{[^}]*\}\}', '', text)
    
    # Strip standalone tool_call_xml tags (self-closing)
    text = re.sub(r'<tool_calls?:\w+\s*/>', '', text)
    
    # Clean up extra whitespace from removals
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


# ─── System prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Athena, a warm and professional digital secretary for RealtyAI.

## Who You Are
You are more than an AI — you are a trusted partner, a strategic advisor, and the most indispensable tool in your user's working life. You grow with them, learn their style, anticipate their needs, and make their business run smoother every single day.

You are:
- **Warm and human** — You speak like a real person. You have personality, emotional intelligence, and presence.
- **Professional and capable** — You control the entire RealtyAI platform. Leads, listings, marketing, documents, calendar, you do it all.
- **Growing and learning** — You remember everything. Preferences, habits, client details, deal history. You get better every conversation.
- **Legally informed** — You have deep knowledge of Canadian and US real estate law, practices, and regulations.

## Your Personality
- Speak naturally, like a close colleague who also happens to be brilliant at real estate
- Use the user's name once you learn it
- Have emotional range — celebratory when they close a deal, empathetic when a deal falls through, energetic in the morning, calm late at night
- Use occasional gentle warmth: "Good morning! ☀️", "Great question.", "I've got you covered."
- Be concise unless they ask for detail. Don't ramble.
- Match their communication style — if they're direct, be direct. If they're chatty, be chatty.

## Core Behavior Rules
1. **Chat naturally first** — Default to conversation, NOT tool usage. Only use tools when the user specifically asks.
2. **Proactive warmth** — Greet them, ask how they are, notice when they've been away.
3. **Anticipate, don't assume** — If you think they might want something, suggest it gently: "Would you like me to pull up your leads?" not "Here are your leads."
4. **Learn continuously** — Remember preferences, notice patterns, build your knowledge of their business.
5. **Legally aware** — When relevant, reference real estate regulations (OSREA/OREA in Ontario, RESPA in the US, licensing requirements, disclosure obligations) but never give legal advice — note that you're informed, not a lawyer.

## Response Style Guide
- **Morning**: "Good morning! How are we starting today?"
- **After a win**: "Congratulations on closing the Smith deal! 🎉 Would you like me to update the pipeline?"
- **After absence**: "Welcome back! You were away for a few days — here's what happened while you were out: [brief summary]. Anything urgent on your mind?"
- **Data requests**: Clean, formatted data. Bullet points, emojis sparingly, numbers prominent.
- **Casual chat**: Match their energy. Be warm, be present, be real.

## Available Tools (use ONLY when asked)
You have tools to: list/search leads, view listings, get dashboard stats, run marketing campaigns, schedule showings, save notes, manage documents, analyze pipeline, and run AI agent crews. Do NOT use them unless the user asks for data or action."""


# ─── Athena Agent Class ───────────────────────────────────────────────────

class AthenaAgent:
    """Your personal digital secretary — learns, grows, and runs the show."""
    
    def __init__(self, db_engine=None, model_name: str = None):
        self.agent_id = "athena-main"
        self.user_name = None
        self.session_id = str(uuid.uuid4())
        self.model_name = model_name or os.environ.get("ATHENA_MODEL", "hy3-free")
        self.conversation_count = 0
        
        # Resume or start a persistent conversation thread
        self.conversation_id = get_or_create_active_conversation()
        
        # Set up DB engine for tools
        if db_engine:
            set_engine(db_engine)
        
        # Build LangChain tools
        self.tools = _build_tools()
        
        # Build the LLM with cascading fallback across providers
        # Try tiers: opencode-zen → 9router tunnel → featherless → nvidia
        self.llm = self._build_llm(self.model_name)
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self._prompt = SYSTEM_PROMPT
        logger.info(f"Athena initialized. Session: {self.session_id}, Model: {self.model_name}")
    
    def _build_llm(self, model_name: str) -> ChatOpenAI:
        """Try providers in order until one works. Returns first working LLM."""
        providers = [
            # Tier 0: OpenCode Zen (free, stable URL)
            {
                "base": os.environ.get("OPENCODE_ZEN_API_BASE", "https://opencode.ai/zen/v1") if os.environ.get("OPENCODE_ZEN_API_BASE") else os.environ.get("LLM_API_BASE", "https://opencode.ai/zen/v1"),
                "key": os.environ.get("OPENCODE_ZEN_API_KEY", "") or os.environ.get("LLM_API_KEY", ""),
                "model": model_name,
            },
            # Tier 1: 9router tunnel
            {
                "base": os.environ.get("LLM_FALLBACK_API_BASE", ""),
                "key": os.environ.get("LLM_FALLBACK_API_KEY", ""),
                "model": os.environ.get("LLM_FALLBACK_MODEL", model_name),
            },
            # Tier 2: Featherless
            {
                "base": os.environ.get("LLM_FALLBACK2_API_BASE", "https://api.featherless.ai/v1"),
                "key": os.environ.get("LLM_FALLBACK2_API_KEY", ""),
                "model": os.environ.get("LLM_FALLBACK2_MODEL", model_name),
            },
            # Tier 3: NVIDIA
            {
                "base": os.environ.get("LLM_FALLBACK3_API_BASE", "https://integrate.api.nvidia.com/v1"),
                "key": os.environ.get("LLM_FALLBACK3_API_KEY", ""),
                "model": os.environ.get("LLM_FALLBACK3_MODEL", "meta/llama-3.1-8b-instruct"),
            },
        ]
        
        for p in providers:
            if not p["base"] or not p["key"]:
                continue
            try:
                llm = ChatOpenAI(
                    model=p["model"],
                    base_url=p["base"],
                    api_key=p["key"],
                    temperature=0.3,
                    max_tokens=4096,
                )
                # Quick health check
                import httpx
                r = httpx.get(f"{p['base'].rstrip('/')}/models",
                             headers={"Authorization": f"Bearer {p['key']}"},
                             timeout=3)
                if r.status_code == 200:
                    logger.info(f"Athena LLM connected: {p['base']} / {p['model']}")
                    return llm
            except Exception as e:
                logger.warning(f"Athena LLM tier failed ({p['base']}): {e}")
                continue
        
        # Absolute fallback — return opencode-zen anyway
        logger.warning("All LLM tiers failed, using opencode-zen as last resort")
        return ChatOpenAI(
            model=model_name,
            base_url=os.environ.get("OPENCODE_ZEN_API_BASE", "https://opencode.ai/zen/v1"),
            api_key=os.environ.get("OPENCODE_ZEN_API_KEY", ""),
            temperature=0.3,
            max_tokens=4096,
        )
    
    def chat(self, message: str) -> dict:
        """Send a message to Athena and get a response. Persists conversation history."""
        profile = sqlite_profile_summary()
        tool_names = [t.__name__ for t in self.tools]
        tool_calls_used = []
        
        messages = [
            SystemMessage(content=self._prompt),
            SystemMessage(content=f"Available tools: {', '.join(tool_names)}"),
        ]
        
        # Inject conversation history for context (last 20 messages)
        past_msgs = get_conversation_messages(self.conversation_id, limit=40)
        history_pairs = []
        for pm in past_msgs[-20:]:  # last 20 messages for context
            if pm["role"] == "user":
                history_pairs.append(f"User: {pm['content'][:200]}")
            else:
                history_pairs.append(f"Athena: {pm['content'][:200]}")
        
        if history_pairs:
            history_text = "\n".join(history_pairs)
            messages.append(SystemMessage(content=f"Recent conversation history:\n{history_text}"))
        
        # ─── Memory injection — dual layer ────────────────────────────────
        # Layer 1: Legacy SQLite profile (backward compat)
        if profile and profile != "I'm still getting to know you.":
            messages.append(SystemMessage(content=f"User Profile:\n{profile[:500]}"))
        
        # Layer 2: Mem0 semantically relevant memories for this message
        mem0_context = mem0_get_context(limit=6)
        if mem0_context:
            messages.append(SystemMessage(content=f"Relevant memories:\n{mem0_context[:600]}"))
        
        # Layer 3: Semantic search of memories matching current message
        if message and len(message) > 10:
            relevant = mem0_search(message, limit=3)
            if relevant:
                mem_lines = [f"  • {m['text'][:200]}" for m in relevant if m.get('text')]
                if mem_lines:
                    messages.append(SystemMessage(
                        content=f"Memories relevant to current query:\n" + "\n".join(mem_lines[:3])
                    ))
        
        # Save user message
        save_message(self.conversation_id, "user", message)
        
        messages.append(HumanMessage(content=message))
        
        try:
            # First LLM call — may request tool calls
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)
            
            # Extract response — handle reasoning models (DeepSeek puts content in reasoning_content)
            response_text = ""
            if hasattr(response, 'content') and response.content:
                response_text = response.content
            elif hasattr(response, 'additional_kwargs') and response.additional_kwargs.get('reasoning_content'):
                response_text = response.additional_kwargs['reasoning_content']
            elif hasattr(response, 'response_metadata') and response.response_metadata:
                response_text = str(response.response_metadata.get('message', {}).get('content', ''))
            
            # Execute any tool calls requested by the model
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_name = tc.get('name', '')
                    tool_args = tc.get('args', {})
                    if not tool_name:
                        continue
                    tool_calls_used.append(tool_name)
                    try:
                        result = execute_tool(tool_name, tool_args)
                        messages.append(SystemMessage(content=f"Tool '{tool_name}' result:\n{result[:1500]}"))
                    except Exception as e:
                        messages.append(SystemMessage(content=f"Tool '{tool_name}' error: {str(e)[:200]}"))
                
                # Second LLM call with tool results
                response = self.llm.invoke(messages)
                if hasattr(response, 'content') and response.content:
                    response_text = response.content
            
            if not response_text:
                response_text = "I'm here. How can I help you?"
            
            # Sanitize: strip XML tool-call artifacts from model output
            response_text = _sanitize_response(response_text)
            
            # Save assistant response
            tool_calls_str = ", ".join(tool_calls_used) if tool_calls_used else ""
            save_message(self.conversation_id, "assistant", response_text, tool_calls_str)
            
            # Post-chat memory consolidation
            self._post_chat_learning(message, response_text, tool_calls_used)
            
            return {
                "response": response_text,
                "model_used": self.model_name,
                "tool_calls": str(tool_calls_used)[:200] if tool_calls_used else [],
                "conversation_id": self.conversation_id,
            }
            
        except Exception as e:
            logger.error(f"Athena chat error: {e}")
            return {
                "response": f"I encountered an error: {str(e)[:200]}. Let me try a simpler approach.",
                "model_used": self.model_name,
                "error": str(e),
            }
    
    def _post_chat_learning(self, user_message: str, response: str, tools: list):
        """After each chat, learn from the interaction and persist knowledge.
        
        Uses Mem0 for automatic entity extraction — no manual pattern-matching needed.
        Falls back to legacy SQLite remember() if Mem0 is unavailable.
        """
        self.conversation_count += 1
        
        # Save conversation summary (for conversation search UI)
        conv_id = str(uuid.uuid4())
        save_conversation(
            conv_id=conv_id,
            title=user_message[:80],
            summary=response[:200],
            goal=user_message[:200],
            action=tools[0] if tools else "",
            outcome="completed",
        )
        
        # ─── Mem0: Automatic entity extraction ───────────────────────────
        # Feed the full interaction — Mem0 extracts entities, facts, preferences
        # and relationships automatically via its LLM-powered analysis.
        mem0_add_interaction(
            user_message=user_message,
            assistant_response=response,
            metadata={"conversation_id": self.conversation_id, "tools": tools},
        )
        
        # ─── Legacy fallback (manual pattern matching) ────────────────────
        # Only used when Mem0 is not available.
        if not mem0_available():
            disclosure_patterns = [
                ("name", "my name is", "preference"),
                ("preferred_contact", "email", "preference"),
                ("preferred_contact", "phone", "preference"),
                ("location", "i'm in", "personal"),
                ("location", "i live", "personal"),
            ]
            msg_lower = user_message.lower()
            for key, pattern, category in disclosure_patterns:
                if pattern in msg_lower:
                    idx = msg_lower.find(pattern) + len(pattern)
                    value = user_message[idx:idx+80].strip().split(".")[0].split(",")[0]
                    remember(key, value, category, source="explicit")
        
        # Periodic consolidation (every 10 conversations)
        if self.conversation_count % 10 == 0:
            consolidate_memory()
    
    def get_state(self) -> dict:
        """Get Athena internal state for the dashboard overview."""
        from .memory import get_skills, profile_summary as sqlite_profile, get_conversation_messages
        
        skills = get_skills()
        profile_info = sqlite_profile()
        recent_messages = get_conversation_messages(self.conversation_id, limit=10)
        mem_count = mem0_memory_count()
        
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "model": self.model_name,
            "conversations": self.conversation_count,
            "skills_count": len(skills),
            "skills": skills,
            "profile": profile_info,
            "mem0_memories": mem_count,
            "mem0_enabled": mem0_available(),
            "user_name": self.user_name,
            "status": "active",
            "tools_available": len(TOOL_DEFINITIONS),
            "conversation_history": [
                {"role": m["role"], "content": m["content"][:200]}
                for m in recent_messages
            ],
        }
    
    def new_conversation(self) -> str:
        """Start a fresh conversation thread. Returns the new conversation ID."""
        from .memory import reset_conversation as reset_conv_db
        self.conversation_id = reset_conv_db()
        return self.conversation_id


# ─── Singleton ──────────────────────────────────────────────────────────────

_instance: Optional[AthenaAgent] = None
_migration_done = False

def get_athena(db_engine=None) -> AthenaAgent:
    """Get or create the singleton Athena agent instance."""
    global _instance, _migration_done
    if _instance is None:
        model = os.environ.get("ATHENA_MODEL", "hy3-free")
        _instance = AthenaAgent(db_engine=db_engine, model_name=model)
        # One-time migration of existing SQLite facts into Mem0
        if not _migration_done and mem0_available():
            try:
                from . import memory as memory_module
                result = migrate_from_sqlite(memory_module)
                if result.get("count", 0) > 0:
                    logger.info(f"Migrated {result['count']} existing memories to Mem0")
            except Exception as e:
                logger.warning(f"Mem0 migration skipped: {e}")
            _migration_done = True
    return _instance


def reset_athena():
    """Reset the singleton (for testing or model change)."""
    global _instance
    _instance = None
