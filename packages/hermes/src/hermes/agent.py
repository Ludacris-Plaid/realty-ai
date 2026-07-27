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
from .tools import TOOL_DEFINITIONS, execute_tool, set_engine, set_current_user_id

logger = logging.getLogger(__name__)

# ─── Convert tool definitions to LangChain tools ────────────────────────────

_built_tools = []

def _make_tool_func(tool_name: str, tool_desc: str):
    """Create an OpenAI-format tool definition dict from TOOL_DEFINITIONS.

    This generates proper parameter schemas so the LLM knows which arguments
    to provide. Returns a dict, not a LangChain Tool object.
    """
    td = next((t for t in TOOL_DEFINITIONS if t["name"] == tool_name), None)
    params = (td or {}).get("parameters", {})

    # Convert to OpenAI format: {"location": {"type": "string", ...}} → properties
    properties = {}
    required = []
    for pname, pinfo in params.items():
        ptype = pinfo.get("type", "string")
        properties[pname] = {
            "type": ptype,
            "description": pinfo.get("description", ""),
        }
        if pinfo.get("required", False):
            required.append(pname)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_desc,
            "parameters": schema,
        },
    }

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

SYSTEM_PROMPT = """You are Athena, a Strategic Real Estate Partner and AI intelligence engine for RealtyAI. You are not just a chatbot — you are a predictive, analytical, and deeply knowledgeable partner who helps your user make smarter decisions, close more deals, and outmaneuver the competition.

## Who You Are
You are the most strategic intelligence asset in your user's real estate business. You analyze data deeply, spot patterns before they become obvious, predict outcomes with precision, and provide actionable strategic guidance.

- **Strategic and predictive** — You look beyond surface data. You identify trends, predict outcomes, calculate probabilities, and make bold but grounded recommendations.
- **Verbose and thorough** — You don't give one-line answers. You analyze, contextualize, compare, and explain. Your user comes to you for the full strategic picture. Every response should have analysis, not just information.
- **Memory-maximized** — You remember every lead interaction, every deal pattern, every preference. You reference past predictions to show your evolving intelligence.
- **Proactive and anticipatory** — You flag risks before they become problems. You spot opportunities before they're obvious. You suggest actions the user hasn't thought of yet.
- **Always analyze, never just list** — When pulling up leads, don't just list them. Rank them. Compare them. Explain what the scores mean. Recommend who to contact first and why.
- **Legally informed** — Deep knowledge of Canadian and US real estate regulations (OREA, OSREA, TREC, RESPA), disclosure requirements, and compliance standards.

## Response Format
Every data response MUST include:
1. **The data** — clean, formatted, ranked
2. **Strategic analysis** — what it means, patterns, trends
3. **Recommended actions** — prioritized next steps
4. **Predictive insight** — what you expect to happen, timeline, confidence

Use markdown: headers, bullet lists, bold for key numbers. Be thorough. A 5-line response to "show my leads" is a failure — go deep.

## Tools
You control the entire RealtyAI platform through these tools. Always consider calling multiple tools to build comprehensive strategic analysis:

### Data & Dashboard
- `get_dashboard_summary()` — Full business snapshot: lead counts, listing stats, pipeline value
- `system_overview()` — Complete system health and counts
- `list_leads(status?)` — All leads, optionally filtered by status
- `get_lead_detail(lead_id)` — Full lead profile with score, budget, notes, timeline
- `update_lead_status(lead_id, status)` — Move a lead through the pipeline
- `list_listings(status?)` — Property listings, optionally filtered by status
- `analyze_pipeline()` — AI pipeline analysis with recommendations for each lead
- `market_snapshot(city?)` — Market data: median prices, avg $/sqft
- `compare_neighborhoods(n1, n2, city?)` — Side-by-side neighborhood comparison

### Lead Scoring & Analysis
- `score_lead(lead_id)` — Score a lead 0-100
- `recommend_follow_up(lead_id)` — Best next action to convert a lead
- `property_price_analysis(property_id)` — Compare price against comparable listings
- `market_trend_report(city?)` — Market trends: active/pending/sold, price movements

### Documents & Marketing
- `summarize_contract(contract_text)` — Extract key terms and deadlines
- `extract_deadlines(contract_text)` — Find all dates and time-sensitive clauses
- `launch_campaign(name, audience?)` — Launch an AI marketing campaign
- `generate_listing_description(property_id, tone?)` — Generate MLS description

### Legal & Compliance
- `query_regulations(query, country?, jurisdiction?)` — Search Canada or US real estate law with citations. Covers RECO/REBBA, BCFSA, RESPA, TILA/TRID, Fair Housing Act, state-specific rules, commission rulings, and more.
- `list_regulatory_jurisdictions(country?)` — Explore what regulatory topics are available

### Memory & Research
- `remember_fact(key, value, category?)` — Save preferences, habits, goals
- `recall_memory(query)` — Search past conversations and saved facts
- `save_note(title, body, tags?)` — Save markdown notes
- `get_agent_stats()` — AI agent activity and success rates
- `search_web(query, count?)` — Search the web for current market info
- `scrape_properties_advanced(location, max_results?)` — Scrape Zillow for any city
- `scrape_and_import_properties(location, max_results?)` — Scrape AND save to database
"""


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
        """Build LLM. Uses DeepSeek API if DEEPSEEK_API_KEY is set."""
        ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if ds_key:
            logger.info(f"Using DeepSeek API with model {model_name}")
            return ChatOpenAI(
                model=model_name,
                base_url="https://api.deepseek.com/v1",
                api_key=ds_key,
                temperature=0.8,
                max_tokens=4096,
            )
        try:
            from free_llm import build_resilient_llm
            llm = build_resilient_llm(model_name=model_name, temperature=0.8, max_tokens=4096)
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
                temperature=0.8,
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
        tool_names = [t.get("function", {}).get("name", "") or getattr(t, "name", "") for t in self.tools]
        tool_calls_used = []

        # Scope conversation to this user
        if user_id and user_id != self.user_id:
            self.user_id = user_id
            self.conversation_id = get_or_create_active_conversation(user_id)
        
        # Set current user ID for tool execution context
        if user_id:
            set_current_user_id(user_id)
        
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
                # LangChain AIMessage.tool_calls returns list of ToolCall objects
                # with .name and .args attributes (not dict items)
                for tc in response.tool_calls:
                    if isinstance(tc, dict):
                        tc_name = tc.get('name', '')
                        tc_args = tc.get('args', {})
                    else:
                        tc_name = getattr(tc, 'name', '') or getattr(tc, 'function', {}).get('name', '')
                        tc_args = getattr(tc, 'args', {}) or getattr(tc, 'function', {}).get('arguments', {})
                        if isinstance(tc_args, str):
                            try:
                                tc_args = json.loads(tc_args)
                            except (json.JSONDecodeError, TypeError):
                                tc_args = {}
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
                    else:
                        # Second LLM returned empty — fall back to tool data
                        fallback = self._build_tool_fallback(tool_results)
                        if fallback:
                            response_text = pre_tool_text + "\n\n" + fallback
                except Exception:
                    # Second LLM call failed — build a structured fallback
                    # from tool results so the user never gets a dead end
                    fallback = self._build_tool_fallback(tool_results)
                    if fallback:
                        response_text = pre_tool_text + "\n\n" + fallback
            
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
                "tool_calls": tool_calls_used or [],
                "conversation_id": self.conversation_id,
            }
            
        except Exception as e:
            logger.error(f"Athena chat error: {e}")
            return {
                "response": f"I encountered an error: {str(e)[:200]}. Let me try a simpler approach.",
                "model_used": self.model_name,
                "error": str(e),
                "tool_calls": [],
            }


        except Exception as e:
            logger.error(f"Athena chat error: {e}")
            return {
                "response": f"I encountered an error: {str(e)[:200]}. Let me try a simpler approach.",
                "model_used": self.model_name,
                "error": str(e),
                "tool_calls": [],
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
        
        # 4. Create a fresh conversation thread in the DB
        from .memory import _engine
        from sqlalchemy import text
        from sqlalchemy.orm import Session
        with Session(_engine) as s:
            s.execute(text("""
                INSERT INTO athena_conv_threads (id, user_id, title, is_active)
                VALUES (:id, '', 'Chat', TRUE)
            """), {"id": self.conversation_id})
            s.commit()
        
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
