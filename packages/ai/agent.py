"""
RealtyAI — Multi-Agent Orchestrator.

Architecture:
    User → Supervisor → Specialist Agent → Response

The Supervisor classifies intent and routes to the right agent:
  - Lead Agent: qualifying, scoring, follow-ups
  - Marketing Agent: campaigns, social, content
  - Listing Agent: MLS descriptions, comparisons
  - Transaction Agent: deadlines, contracts
  - Document Agent: contract analysis, RAG
  - Research Agent: market trends, neighborhoods
  - General Assistant: fallback for anything else

Provider fallback: Featherless → NVIDIA on capacity/rate-limit errors.
"""
import logging
from typing import Optional

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT
from llm_config import get_model, get_fast_model, get_primary_model, get_fallback_model
from router import classify_task
from agents.supervisor import route, get_agent_tools, AGENT_REGISTRY
from activity import record_activity

logger = logging.getLogger(__name__)

# ─── Base Agent Factory ─────────────────────────────────────────────────────

def build_agent(model_name: Optional[str] = None, extra_tools: Optional[list] = None, force_fallback: bool = False):
    """Create a ReAct agent with domain-specific tools.
    
    Args:
        model_name: Model ID override.
        extra_tools: Additional tools for this specialist agent.
        force_fallback: Use NVIDIA fallback instead of primary provider.
    """
    if force_fallback:
        llm = get_fallback_model()
    else:
        llm = get_model(model_name or get_fast_model())
    tools = list(ALL_TOOLS)
    if extra_tools:
        tools.extend(extra_tools)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )


# ─── Multi-Agent Invocation ─────────────────────────────────────────────────

def ask(message: str, override_model: Optional[str] = None) -> dict:
    """Send a message to the multi-agent system.
    
    1. Supervisor classifies the intent
    2. Routes to the right specialist with their tools
    3. Executes and returns the response
    4. Records the activity
    
    Falls back to NVIDIA if Featherless returns capacity/rate-limit errors.
    
    Args:
        message: The user's message.
        override_model: Force a specific model.
    
    Returns:
        dict with keys: messages, response, model_used, supervisor
    """
    # Step 1: Supervisor routes
    decision = route(message)
    model_name = override_model or classify_task(message)

    # Step 2: Build specialist agent with their tools
    specialist_tools = get_agent_tools(decision.intent)
    task_agent = build_agent(model_name, extra_tools=specialist_tools)

    # Step 3: Execute — gentle fallback (no hard crash)
    try:
        result = task_agent.invoke(
            {"messages": [HumanMessage(content=message)]}
        )
    except Exception as e:
        err_str = str(e).lower()
        logger.warning(f"Primary model failed ({err_str[:100]}), trying fallback")
        # Try NVIDIA fallback silently (no hard crash if it also fails)
        try:
            fallback_agent = build_agent(model_name, extra_tools=specialist_tools, force_fallback=True)
            result = fallback_agent.invoke(
                {"messages": [HumanMessage(content=message)]}
            )
            model_name = f"{model_name} (via fallback)"
        except Exception as e2:
            # Both providers failed — return graceful error, not a crash
            record_activity(
                agent_name=decision.agent_name,
                action=message[:120],
                intent=decision.intent,
                model_used="failed",
                status=f"error: both providers failed",
            )
            return {
                "messages": [],
                "response": "Both providers are unavailable right now. Please try again in a moment.",
                "model_used": "failed",
                "supervisor": decision.to_dict(),
            }

    messages = result["messages"]
    response_text = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            break

    # Step 4: Record activity
    record_activity(
        agent_name=decision.agent_name,
        action=message[:120],
        intent=decision.intent,
        model_used=model_name,
        status="success",
    )

    return {
        "messages": messages,
        "response": response_text,
        "model_used": model_name,
        "supervisor": decision.to_dict(),
    }
