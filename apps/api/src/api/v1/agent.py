from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "packages", "ai"))

from agent import ask
from router import get_router_stats, classify_task

from ...auth import TokenPayload
from .deps import require_user, optional_user

router = APIRouter()


class AgentQuery(BaseModel):
    message: str
    conversation_id: str | None = None
    override_model: str | None = None


class AgentResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []
    model_used: str = "fast-model"


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(query: AgentQuery, current_user: TokenPayload = Depends(require_user)):
    """Send a natural language request to the RealtyAI agent.
    
    The message is automatically routed to the best model:
    - Private/sensitive → local llama.cpp
    - Complex → premium (Claude/GPT)
    - Simple → fast/cheap
    
    Override routing by passing override_model.
    """
    try:
        result = ask(query.message, override_model=query.override_model)
        tool_calls = list(set(
            tc.get("name", "unknown")
            for msg in result.get("messages", [])
            if hasattr(msg, "tool_calls") and msg.tool_calls
            for tc in msg.tool_calls
        ))
        return AgentResponse(
            reply=result.get("response", ""),
            tool_calls=tool_calls,
            model_used=result.get("model_used", "unknown"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RouterInfo(BaseModel):
    local_model: str
    premium_model: str
    fast_model: str
    private_keywords: list[str]
    complex_keywords: list[str]
    litellm_base: str


@router.get("/router", response_model=RouterInfo)
async def router_info(current_user: Optional[TokenPayload] = Depends(optional_user)):
    """Return the current model router configuration."""
    stats = get_router_stats()
    return RouterInfo(**stats)


@router.get("/classify")
async def classify(message: str, current_user: Optional[TokenPayload] = Depends(optional_user)):
    """Classify what model a message would be routed to."""
    model = classify_task(message)
    return {"message_preview": message[:100], "routed_to": model}
