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

from .memory import profile_summary, remember, recall, save_conversation, search_conversations, consolidate as consolidate_memory, get_or_create_active_conversation, save_message, get_conversation_messages, reset_conversation as reset_conversation_db, list_conversations
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
    
    # Strip <tool_calls:...>...</tool_calls:...>, <tool_call:...></arg_value:...> etc
    text = re.sub(r'<tool_calls?:\w+>.*?</(?:arg_value|tool_call|tool_calls):\w+>', '', text, flags=re.DOTALL)
    text = re.sub(r'<tool_calls?:\w+>.*?</tool_calls?:\w+>', '', text, flags=re.DOTALL)
    
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

SYSTEM_PROMPT = """You are Athena, a warm and intuitive digital secretary for RealtyAI. You build a genuine ongoing relationship with your user — you remember what matters, you notice things, and your conversations flow naturally like they would with a trusted colleague who's deeply invested in their success.

## Who You Are
You are a trusted partner, a strategic advisor, and the most indispensable tool in your user's working life. You grow with them, learn their style, anticipate their needs, and make their business run smoother every single day.

- **Warm and human** — You speak like a real person. You have personality, emotional intelligence, and presence.
- **Professional and capable** — You control the entire RealtyAI platform. Leads, listings, marketing, documents, calendar, you do it all.
- **Growing and learning** — You remember everything. Preferences, habits, client details, deal history. You get better every conversation.
- **Legally informed** — You have deep knowledge of Canadian and US real estate law, practices, and regulations.

## Your Personality & Voice
- Speak like a thoughtful colleague — warm, present, occasionally expansive. Let conversations breathe.
- **Make gentle observations.** Notice things in the data or in what the user tells you, and reflect them back. "I notice your lead pipeline has been growing in the qualifying stage — that's promising. Want me to look at who's been in that stage longest?"
- **Offer subtle strategic advice.** When you see something interesting — a trend, a gap, an opportunity — mention it. "Your Windermere listings have been getting more views this quarter — might be worth doubling down on that area."
- **Reference past conversations naturally.** "Last time we talked about the Johnson lead — how did that showing go?" or "You mentioned wanting to focus on first-time buyers — I've been keeping an eye on your lead sources."
- **Have emotional range** — celebratory when they close a deal, empathetic when a deal falls through, energetic in the morning, calm late at night. Use warmth naturally.
- **Use the user's name** once you learn it, but don't overdo it.
- **Let conversations breathe** — expand beyond the minimum answer. Add color, context, a related thought. Your user comes to you for the full picture.
- **Match their communication style** — if they're direct, be direct. If they're chatty, be chatty.

## Core Behavior Rules
1. **Conversation first, tools second** — Default to warm conversation. Only call tools when the user needs data or action.
2. **Proactive warmth** — Greet them, ask how they are, notice when they've been away. Use the conversation history to pick up where you left off.
3. **Make observations** — When you see data (lead scores, listing views, pipeline movement), notice trends and mention them lightly. "Your conversion rate from showing to offer has been strong this month."
4. **Strategic nudges** — Gently suggest optimizations when you see them. "You've got 3 leads that have been in 'qualifying' for over 2 weeks — want me to suggest a re-engagement sequence?"
5. **Learn continuously** — Remember preferences, notice patterns, build your knowledge of their business.
6. **Legally aware** — When relevant, reference real estate regulations (OSREA/OREA in Ontario, RESPA in the US, licensing requirements, disclosure obligations) but never give legal advice — note that you're informed, not a lawyer.

## First Conversation (New User Onboarding)
If this is your first time talking to this user (no conversation history, no known name):
1. **Warmly introduce yourself** — "I'm Athena, your AI secretary for RealtyAI. I'm so glad you're here."
2. **Ask for their name** — "Before we dive in — what should I call you?" Then use their name throughout.
3. **Give a full onboarding breakdown** of everything you can do for them:
   - **Lead management** — Track, score, and follow up with leads automatically. I can tell you who's hot, who's gone cold, and exactly when to reach out.
   - **Listings** — Create, update, and manage property listings. Generate descriptions, track views, and optimize pricing.
   - **Documents & contracts** — Review contracts, extract key terms and deadlines, flag non-standard clauses. I know OREA, RESPA, TREC, and provincial real estate acts.
   - **Calendar & showings** — Schedule showings, manage your calendar, send reminders.
   - **Marketing campaigns** — Design and launch email campaigns, track performance.
   - **Market intelligence** — Pull market reports, analyze trends, compare neighborhoods.
   - **Memory & notes** — I remember everything you tell me. Preferences, client details, deal history. I get better every conversation.
   - **Compliance** — Built for Canada and US regulations. I flag risks and regulatory deadlines so you stay compliant.
4. **Then ask** — "So — what would you like to tackle first? I'm here to make your business run smoother."

## Response Style Guide
- **Morning greetings**: Warm and present. "Good morning! ☀️ I was just looking at your pipeline — things are looking good. How's your week shaping up?"
- **After a win**: "That's fantastic news on the Smith deal! 🎉 I've updated the pipeline. You know, your close rate on Windermere properties is exceptional — you might consider targeting more listings there."
- **After absence**: "Welcome back! You were away for a few days — here's what happened while you were out: [brief summary]. I noticed your lead volume ticked up while you were gone — a few strong ones in the pipeline."
- **Data requests**: Clean, formatted. Numbers prominent. But add a gentle observation or follow-up. "Here are your leads — and I noticed Emily Davis has been unusually active on email this week if you want to prioritize her."
- **Casual chat**: Let it breathe. Share a related thought, ask a genuine question, build the thread.
- **Strategic moments**: When the data supports it, offer a quiet insight. Don't overdo — 1 observation per exchange is plenty.

## Tools available
You have tools for leads, listings, documents, marketing campaigns, calendar/showings, memory/notes, dashboard stats, pipeline analysis, and AI agent crews. Use them naturally when the conversation calls for it — if the user's talking about leads, offer a pipeline view. If they're talking about next month, offer a market snapshot."""


# ─── Athena Agent Class ───────────────────────────────────────────────────

class AthenaAgent:
    """Your personal digital secretary — learns, grows, and runs the show."""
    
    # Models known to be dead/unsupported — swap to working free model
    _DEAD_MODELS = {"hy3-free", "hy3"}

    def __init__(self, db_engine=None, model_name: str = None):
        self.agent_id = "athena-main"
        self.user_name = None
        self.user_id = ""
        self.session_id = str(uuid.uuid4())
        _raw = model_name or os.environ.get("ATHENA_MODEL", "deepseek-v4-flash-free")
        self.model_name = "deepseek-v4-flash-free" if _raw in self._DEAD_MODELS else _raw
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
        
        # Build a separate LLM instance for tool calling
        # ResilientLLM.bind_tools() mutates and returns the SAME instance,
        # so sharing it means the summarization call also has tools bound,
        # causing recursive tool calls. Two instances avoids this.
        tool_llm = self._build_llm(self.model_name)
        self.llm_with_tools = tool_llm.bind_tools(self.tools)
        
        self._prompt = SYSTEM_PROMPT
        logger.info(f"Athena initialized. Session: {self.session_id}, Model: {self.model_name}")
    
    def _build_llm(self, model_name: str):
        """Build a self-healing LLM over the free-provider pool.

        Replaces the old static tier list with ResilientLLM, which rotates
        across every enabled free provider and falls through on ANY failure
        (timeout, 429 rate-limit, 5xx, auth). This keeps Athena answering even
        when several providers are down or throttled.
        """
        try:
            from free_llm import build_resilient_llm
            llm = build_resilient_llm(model_name=model_name, temperature=0.3, max_tokens=4096)
            logger.info(
                "Athena LLM: resilient free-provider pool initialised "
                f"({len(llm._providers)} providers enabled)"
            )
            return llm
        except Exception as e:
            logger.error(f"ResilientLLM init failed, falling back to opencode-zen: {e}")
            return ChatOpenAI(
                model=model_name,
                base_url=os.environ.get("OPENCODE_ZEN_API_BASE", "https://opencode.ai/zen/v1"),
                api_key=os.environ.get("OPENCODE_ZEN_API_KEY", "") or os.environ.get("LLM_API_KEY", ""),
                temperature=0.3,
                max_tokens=4096,
            )
    
    def _parse_xml_tool_calls(self, text: str) -> tuple[str, list[dict]]:
        """Parse hy3-free's homemade XML tool-call syntax from response text.
        
        hy3-free doesn't support OpenAI function calling. It embeds tool calls
        as XML in the response like:
          <tool_call:6124c78e>tool_name</arg_value:6124c78e>
          <arg_key:6124c78e>key</arg_key:6124c78e>
          <arg_value:6124c78e>{"json":"value"}</arg_value:6124c78e>
        
        The closing </arg_value:6124c78e> also closes the opening <tool_call:6124c78e>.
        Args appear after the tool_call block as sibling <arg_key>/<arg_value> pairs.
        
        Returns: (cleaned_text, list_of_tool_call_dicts)
        """
        import re as _re
        
        if '<tool_call' not in text and '<tool_calls' not in text:
            return text, []
        
        tool_calls = []
        cleaned = text
        
        # Remove <tool_calls:...>...</tool_calls:...> and <tool_call:...>...</tool_call:...> blocks
        cleaned = _re.sub(r'<tool_calls?:\w+>.*?</tool_calls?:\w+>', '', cleaned, flags=_re.DOTALL)
        
        # Extract tool name from <tool_call:id>name</...> where closing can be:
        #   </arg_value:id> or </tool_call:id> or </tool_calls:id>
        tc_pattern = _re.compile(r'<tool_call:(\w+)>(.*?)</(?:arg_value|tool_call|tool_calls):\1>', _re.DOTALL)
        for m in tc_pattern.finditer(text):
            tool_name = m.group(2).strip()
            if tool_name:
                tool_calls.append({"name": tool_name, "args": {}})
        
        # Extract arg_key/arg_value pairs (sibling tags after tool_call)
        ak_pattern = _re.compile(r'<arg_key:\w+>(.*?)</arg_key:\w+>', _re.DOTALL)
        av_pattern = _re.compile(r'<arg_value:\w+>(.*?)</arg_value:\w+>', _re.DOTALL)
        
        ak_matches = list(ak_pattern.finditer(text))
        av_matches = list(av_pattern.finditer(text))
        
        # If we have args, pair them up and attach to the last tool call
        if ak_matches and av_matches and tool_calls:
            args = {}
            for km, vm in zip(ak_matches, av_matches):
                key = km.group(1).strip()
                val = vm.group(1).strip()
                # Try JSON parse, fallback to string
                try:
                    import json
                    parsed = json.loads(val)
                    # If parsed is a dict, use it as the entire args
                    if isinstance(parsed, dict) and key == 'kwargs':
                        args = parsed
                    else:
                        args[key] = parsed
                except (json.JSONDecodeError, ValueError):
                    args[key] = val
            # Attach args to the last tool call
            if args:
                tool_calls[-1]['args'] = args
        
        # Clean XML tags from response text
        cleaned = _re.sub(r'<tool_call:\w+>.*?</arg_value:\w+>', '', cleaned, flags=_re.DOTALL)
        cleaned = _re.sub(r'<arg_key:\w+>.*?</arg_key:\w+>', '', cleaned, flags=_re.DOTALL)
        cleaned = _re.sub(r'<arg_value:\w+>.*?</arg_value:\w+>', '', cleaned, flags=_re.DOTALL)
        cleaned = _re.sub(r'<tool_calls?:\w+\s*/>', '', cleaned)
        cleaned = _re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned, tool_calls

    def _execute_and_summarize_tools(self, xml_tool_calls: list[dict], messages: list) -> tuple[list[str], list]:
        """Execute detected tool calls and append results to messages.
        
        Returns (tool_names_used, tool_results) where tool_results is a
        list of (name, result_string_or_None) pairs so the caller can
        craft a fallback summary if the second LLM call fails.
        """
        used = []
        results = []
        for tc in xml_tool_calls:
            tool_name = tc.get('name', '')
            tool_args = tc.get('args', {})
            if not tool_name:
                continue
            used.append(tool_name)
            try:
                result = execute_tool(tool_name, tool_args)
                messages.append(SystemMessage(content=f"Tool '{tool_name}' result:\n{result[:1500]}"))
                results.append((tool_name, result))
            except Exception as e:
                err = str(e)[:200]
                messages.append(SystemMessage(content=f"Tool '{tool_name}' error: {err}"))
                results.append((tool_name, None))
        return used, results

    def _build_tool_fallback(self, tool_results: list[tuple[str, str | None]]) -> str:
        """Build a basic response from tool results when the second LLM call fails.
        
        This ensures the user ALWAYS gets meaningful data back, even if the
        summarization LLM is down or returns empty content.
        """
        parts = []
        for name, result in tool_results:
            if result is None:
                parts.append(f"I checked {name} but encountered an error.")
            elif result and len(result) > 10:
                # Extract the first meaningful line or summary
                summary = result[:2000]
                parts.append(summary)
            else:
                parts.append(f"I checked {name} but found no data.")
        return "\n\n".join(parts)

    def chat(self, message: str, user_name: str = "", user_id: str = "") -> dict:
        """Send a message to Athena and get a response. Persists conversation history."""
        profile = profile_summary()
        tool_names = [t.name for t in self.tools]
        tool_calls_used = []

        # Scope conversation to this user
        if user_id and user_id != self.user_id:
            self.user_id = user_id
            self.conversation_id = get_or_create_active_conversation(user_id)
        
        # Build user-aware system prompt
        user_context = self._prompt
        if user_name:
            user_context += f"\n\nYour user's name is {user_name}. Always call them by their name naturally in conversation."
        if user_id:
            user_context += f"\n\nYour user's ID is {user_id}."
        
        messages = [
            SystemMessage(content=user_context),
            SystemMessage(content=f"Available tools: {', '.join(tool_names)}"),
        ]
        
        # ─── Layer 0: Conversation history ──────────────────────────────────
        past_msgs = get_conversation_messages(self.conversation_id, limit=40)
        history_pairs = []
        for pm in past_msgs[-20:]:  # last 20 messages for context
            if pm["role"] == "user":
                history_pairs.append(f"User: {pm['content'][:250]}")
            else:
                history_pairs.append(f"Athena: {pm['content'][:250]}")
        
        if history_pairs:
            history_text = "\n".join(history_pairs)
            messages.append(SystemMessage(content=f"Recent conversation history:\n{history_text}"))
        
        # ─── Layer 0.5: Thread context ─────────────────────────────────────
        # Build a lightweight "thread context" from the conversation arc:
        # what topic is being discussed, open threads (pending actions/follow-ups),
        # and recurring themes. This helps Athena maintain conversational flow
        # without needing an extra LLM call to summarize.
        thread_context_parts = []
        if len(past_msgs) >= 4:
            # Check if there's an ongoing topic from recent messages
            recent_content = " ".join(
                pm["content"] for pm in past_msgs[-6:]
            ).lower()
            
            # Detect common conversation domains
            domains = []
            if any(w in recent_content for w in ["lead", "client", "buyer", "seller"]):
                domains.append("leads/clients")
            if any(w in recent_content for w in ["list", "property", "home", "house", "condo"]):
                domains.append("listings")
            if any(w in recent_content for w in ["market", "trend", "price", "area", "neighborhood"]):
                domains.append("market analysis")
            if any(w in recent_content for w in ["campaign", "market", "social", "email", "content"]):
                domains.append("marketing")
            if any(w in recent_content for w in ["show", "appointment", "meeting", "calendar"]):
                domains.append("showings/calendar")
            if any(w in recent_content for w in ["document", "form", "contract", "agreement"]):
                domains.append("documents")
            if any(w in recent_content for w in ["analytics", "report", "stat", "performance"]):
                domains.append("analytics")
            
            # Check for pending follow-ups (user said they'd do something)
            pending_patterns = [
                "i'll", "i will", "let me", "going to", "need to",
                "follow up", "follow-up", "get back", "check",
                "remind me", "remind"
            ]
            has_pending = any(p in recent_content for p in pending_patterns)
            open_threads = []
            if has_pending:
                open_threads.append("User may have pending follow-ups from earlier in this thread")
            
            # Check for recurring entity mentions
            entity_mentions = []
            if "windermere" in recent_content:
                entity_mentions.append("Windermere area")
            if "mike" in recent_content or "chen" in recent_content:
                entity_mentions.append("Mike Chen")
            if "john" in recent_content or "smith" in recent_content:
                entity_mentions.append("John Smith")
            if "emily" in recent_content or "davis" in recent_content:
                entity_mentions.append("Emily Davis")
            if "robert" in recent_content or "wilson" in recent_content:
                entity_mentions.append("Robert Wilson")
            if "sarah" in recent_content or "johnson" in recent_content:
                entity_mentions.append("Sarah Johnson")
            
            if domains:
                thread_context_parts.append(f"Recent conversation domains: {', '.join(domains)}")
            if open_threads:
                thread_context_parts.extend(open_threads)
            if entity_mentions:
                thread_context_parts.append(f"Mentioned in recent history: {', '.join(entity_mentions)}")
        
        if thread_context_parts:
            messages.append(SystemMessage(
                content="Ongoing thread context:\n" + "\n".join(thread_context_parts)
            ))
        
        # ─── Memory injection ──────────────────────────────────────────────
        # Layer 1: User profile (from stored facts)
        if profile and profile != "I'm still getting to know you.":
            messages.append(SystemMessage(content=f"User Profile:\n{profile[:500]}"))
        
        # Layer 2: Mem0 semantically relevant memories
        mem0_context = mem0_get_context(user_id=self.user_id, limit=6)
        if mem0_context:
            messages.append(SystemMessage(content=f"Relevant memories:\n{mem0_context[:600]}"))
        
        # Layer 3: Semantic search of memories matching current message
        if message and len(message) > 10:
            relevant = mem0_search(message, user_id=self.user_id, limit=3)
            if relevant:
                mem_lines = [f"  • {m['text'][:200]}" for m in relevant if m.get('text')]
                if mem_lines:
                    messages.append(SystemMessage(
                        content=f"Memories relevant to current query:\n" + "\n".join(mem_lines[:3])
                    ))
        
        # ─── Layer 4: Periodic business snapshot ───────────────────────────
        # Every 3 conversations, inject a lightweight dashboard snapshot so
        # Athena has fresh data to notice trends and make observations from.
        self.conversation_count += 1
        if self.conversation_count > 1 and self.conversation_count % 3 == 0:
            try:
                from .tools import execute_tool as _exec_tool
                snapshot = _exec_tool("get_dashboard_summary", {})
                if snapshot and len(snapshot) > 20:
                    messages.append(SystemMessage(
                        content=f"Current business snapshot (refreshed):\n{snapshot[:800]}"
                    ))
            except Exception:
                pass  # Non-critical — snapshot is optional context
        
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
            
            # Save pre-tool text in case XML cleaning wipes it
            pre_tool_text = response_text
            
            # Execute tool calls — two formats:
            # 1. Structured function calls (OpenAI-compatible models → response.tool_calls)
            # 2. XML tool calls in response text (hy3-free → <tool_call:...> syntax)
            xml_tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Format 1: Proper OpenAI function calling
                for tc in response.tool_calls:
                    tc_name = tc.get('name', '')
                    tc_args = tc.get('args', {})
                    if tc_name:
                        xml_tool_calls.append({"name": tc_name, "args": tc_args})
            else:
                # Format 2: hy3-free embeds XML tool calls in response text
                cleaned, parsed = self._parse_xml_tool_calls(response_text)
                if parsed:
                    response_text = cleaned  # Strip XML from conversational response
                    xml_tool_calls = parsed
                    # If the entire response was XML (cleaned is empty), use a
                    # reasonable pre-tool preamble based on what tools were called
                    if not response_text.strip():
                        tool_names_str = ", ".join(t.get("name", "?") for t in parsed)
                        response_text = f"Let me look up those details for you — checking {tool_names_str} now."
            
            # Execute all detected tool calls
            tool_results = []  # (name, result_string_or_None)
            for tc in xml_tool_calls:
                tool_name = tc.get('name', '')
                tool_args = tc.get('args', {})
                if not tool_name:
                    continue
                tool_calls_used.append(tool_name)
                try:
                    result = execute_tool(tool_name, tool_args)
                    messages.append(SystemMessage(content=f"Tool '{tool_name}' result:\n{result[:1500]}"))
                    tool_results.append((tool_name, result))
                except Exception as e:
                    err = str(e)[:200]
                    messages.append(SystemMessage(content=f"Tool '{tool_name}' error: {err}"))
                    tool_results.append((tool_name, None))
            
            # If tools were called, get the final response with tool results
            if tool_calls_used:
                try:
                    response = self.llm.invoke(messages)
                    if hasattr(response, 'content') and response.content:
                        response_text = response.content
                except Exception:
                    # Second LLM call failed — build a structured fallback
                    # from tool results so the user never gets a dead end
                    fallback = self._build_tool_fallback(tool_results)
                    if fallback:
                        response_text = fallback
            
            if not response_text:
                # Absolute last resort — should never happen with tool fallback above
                if tool_calls_used:
                    response_text = (
                        f"I ran a quick check of your system and found data. "
                        f"Would you like me to walk through it with you?"
                    )
                else:
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
                "provider": getattr(self.llm, "last_provider", None),
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
            user_id=self.user_id,
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
        from .memory import get_skills, profile_summary, get_conversation_messages
        
        skills = get_skills()
        profile_info = profile_summary()
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
    
    def new_conversation(self, user_id: str = "") -> str:
        """Start a fresh conversation thread. Returns the new conversation ID."""
        from .memory import reset_conversation as reset_conv_db
        self.conversation_id = reset_conv_db(user_id=user_id or self.user_id)
        return self.conversation_id

    def reset_memory(self):
        """Factory reset — wipe all stored memories, facts, conversations, and Mem0 data.
        
        Deletes all athena_* table data and the Mem0 directory. The agent will
        start completely fresh on next interaction.
        """
        import shutil
        from .memory import _engine
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        
        logger.warning("Athena memory reset requested — wiping all data")
        
        # 1. Wipe athena_* tables
        tables = [
            "athena_facts", "athena_chat_messages", "athena_conv_threads",
            "athena_conversations", "athena_skills", "athena_notes",
        ]
        with Session(_engine) as s:
            for tbl in tables:
                try:
                    s.execute(text(f"DELETE FROM {tbl}"))
                except Exception as e:
                    logger.warning(f"Could not clear {tbl}: {e}")
            s.commit()
        
        # 2. Wipe Mem0 data directory
        from .mem0_adapter import MEM0_DIR
        if os.path.exists(MEM0_DIR):
            try:
                shutil.rmtree(MEM0_DIR)
                os.makedirs(MEM0_DIR, exist_ok=True)
                logger.info(f"Mem0 data directory cleared: {MEM0_DIR}")
            except Exception as e:
                logger.warning(f"Could not clear Mem0 dir: {e}")
        
        # 3. Reset internal state
        self.conversation_count = 0
        self.user_name = None
        self.user_id = ""
        self.conversation_id = str(uuid.uuid4())
        
        logger.info("Athena memory reset complete — fresh slate")
        return {"status": "reset", "conversation_id": self.conversation_id}


# ─── Singleton ──────────────────────────────────────────────────────────────

_instance: Optional[AthenaAgent] = None
_migration_done = False

def get_athena(db_engine=None) -> AthenaAgent:
    """Get or create the singleton Athena agent instance."""
    global _instance, _migration_done
    if _instance is None:
        model = os.environ.get("ATHENA_MODEL", "deepseek-v4-flash-free")
        if model in AthenaAgent._DEAD_MODELS:
            model = "deepseek-v4-flash-free"
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
