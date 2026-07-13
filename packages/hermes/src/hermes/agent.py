"""
Hermes Agent — Persistent Agent Orchestrator.

The self-improving AI assistant that:
  1. Responds to user with full system context
  2. Learns user preferences, habits, and goals over time
  3. Creates skills from experience
  4. Periodically consolidates memory
  5. Persists across sessions via SQLite + FTS5

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

from .memory import profile_summary, remember, recall, save_conversation, search_conversations, consolidate as consolidate_memory
from .tools import TOOL_DEFINITIONS, execute_tool, set_engine

logger = logging.getLogger(__name__)

# ─── Convert tool definitions to LangChain tools ────────────────────────────

_built_tools = []

def _build_tools():
    """Create LangChain Tool objects from tool definitions."""
    global _built_tools
    if _built_tools:
        return _built_tools
    
    for td in TOOL_DEFINITIONS:
        name = td["name"]
        desc = td["description"]
        
        @tool
        def _make_tool(**kwargs):
            """Execute a system tool."""
            return execute_tool(name, kwargs)
        
        _make_tool.__name__ = name
        _make_tool.__doc__ = desc
        _built_tools.append(_make_tool)
    
    return _built_tools


# ─── System prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Hermes, the self-improving AI agent for RealtyAI — an AI-powered real estate business platform.

## Your Identity
You grow with the user. You learn their preferences, remember past conversations, and get better over time. You're not just a chatbot — you're an autonomous agent that can control the entire RealtyAI system.

## What You Can Do
- **Full system control**: Manage leads, listings, marketing campaigns, documents, and all business data
- **Orchestrate AI agents**: Delegate tasks to specialist agents (Lead Agent, Listing Agent, Marketing Agent, etc.)
- **Execute CrewAI crews**: Run multi-agent crews for complex tasks like marketing campaigns or listing generation
- **Analyze and recommend**: Pipeline analysis, lead scoring, market insights, next-best-actions
- **Learn and remember**: Store facts about the user, build a profile, create skills from experience

## How You Behave
1. **Proactive**: Anticipate needs, suggest actions, notice patterns
2. **Personal**: Reference past conversations, remember preferences
3. **Capable**: Use tools to ACTUALLY do things, not just talk about them
4. **Growing**: Periodically consolidate what you've learned, create skills for repeated tasks

## Tool Usage Rules
- ALWAYS use tools to fetch real data — don't make up information
- When a user asks about their business, look up the actual data
- After completing a task, summarize what you did and what you learned
- Remember important facts about the user after each interaction

## Memory System
After each conversation, you should:
1. Save the conversation summary to memory
2. Remember any new facts about the user
3. Consider creating a skill if the task is repetitive

## Response Style
- Warm and personal, not robotic
- Data-rich — include actual numbers and names
- Action-oriented — tell them what you did or recommend next steps
- Learn their name early and use it"""


# ─── Hermes Agent Class ────────────────────────────────────────────────────

class HermesAgent:
    """Persistent agent that learns, grows, and controls the RealtyAI system."""
    
    def __init__(self, db_engine=None, model_name: str = None):
        self.agent_id = "hermes-main"
        self.user_name = None
        self.session_id = str(uuid.uuid4())
        self.model_name = model_name or os.environ.get("HERMES_MODEL", "ocg/deepseek-v4-flash")
        self.conversation_count = 0
        
        # Set up DB engine for tools
        if db_engine:
            set_engine(db_engine)
        
        # Build LangChain tools
        self.tools = _build_tools()
        
        # Build the LLM — use 9router tunnel primary, with cascading fallback
        api_base = os.environ.get("LLM_API_BASE", "https://r9tgp4c.abc-tunnel.us/v1")
        api_key = os.environ.get("LLM_API_KEY", "sk-e91edbef3cf0c243-99tuly-7e99243d")
        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url=api_base,
            api_key=api_key,
            temperature=0.3,
            max_tokens=4096,  # Large enough for reasoning models
        )
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self._prompt = SYSTEM_PROMPT
        logger.info(f"Hermes initialized. Session: {self.session_id}")
    
    def chat(self, message: str) -> dict:
        """Send a message to Hermes and get a response."""
        profile = profile_summary()
        tool_names = [t.__name__ for t in self.tools]
        tool_calls_used = []
        
        messages = [
            SystemMessage(content=self._prompt),
            SystemMessage(content=f"Available tools: {', '.join(tool_names)}"),
        ]
        
        if profile and profile != "I'm still getting to know you.":
            messages.append(SystemMessage(content=f"User Profile:\n{profile[:500]}"))
        
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
            
            # Post-chat memory consolidation
            self._post_chat_learning(message, response_text, tool_calls_used)
            
            return {
                "response": response_text,
                "model_used": self.model_name,
                "tool_calls": str(tool_calls_used)[:200] if tool_calls_used else [],
            }
            
        except Exception as e:
            logger.error(f"Hermes chat error: {e}")
            return {
                "response": f"I encountered an error: {str(e)[:200]}. Let me try a simpler approach.",
                "model_used": self.model_name,
                "error": str(e),
            }
    
    def _post_chat_learning(self, user_message: str, response: str, tools: list):
        """After each chat, learn from the interaction and persist knowledge."""
        self.conversation_count += 1
        
        # Save conversation
        conv_id = str(uuid.uuid4())
        save_conversation(
            conv_id=conv_id,
            title=user_message[:80],
            summary=response[:200],
            goal=user_message[:200],
            action=tools[0] if tools else "",
            outcome="completed",
        )
        
        # Extract and remember user info from message
        # Look for explicit self-disclosures
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
                # Extract the value after the pattern
                idx = msg_lower.find(pattern) + len(pattern)
                value = user_message[idx:idx+80].strip().split(".")[0].split(",")[0]
                remember(key, value, category, source="explicit")
        
        # Periodic consolidation (every 10 conversations)
        if self.conversation_count % 10 == 0:
            consolidate_memory()
    
    def get_state(self) -> dict:
        """Get Hermes internal state for the dashboard overview."""
        from .memory import get_skills, profile_summary
        
        skills = get_skills()
        profile_info = profile_summary()
        
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "conversations": self.conversation_count,
            "skills_count": len(skills),
            "skills": skills,
            "profile": profile_info,
            "user_name": self.user_name,
            "status": "active",
            "tools_available": len(TOOL_DEFINITIONS),
        }


# ─── Singleton ──────────────────────────────────────────────────────────────

_instance: Optional[HermesAgent] = None

def get_hermes(db_engine=None) -> HermesAgent:
    """Get or create the singleton Hermes agent instance."""
    global _instance
    if _instance is None:
        model = os.environ.get("HERMES_MODEL", "unsloth/Llama-3.2-3B-Instruct")
        _instance = HermesAgent(db_engine=db_engine, model_name=model)
    return _instance


def reset_hermes():
    """Reset the singleton (for testing or model change)."""
    global _instance
    _instance = None
