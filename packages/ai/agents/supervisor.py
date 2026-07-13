"""
RealtyAI — Supervisor Agent.

The Supervisor routes user requests to the right specialist agent based on intent.

Architecture:
    User → Supervisor → Intent Classification → Specialist Agent

Intent → Agent mapping:
    lead/qualify/pipeline        → Lead Agent
    marketing/social/campaign    → Marketing Agent
    listing/mls/property/price   → Listing Agent
    transaction/deadline/contract → Transaction Agent
    document/agreement/pdf       → Document Agent
    research/market/neighborhood → Research Agent
    default                      → General Assistant (existing agent.py)
"""
import re
from typing import Optional

from .lead_agent import LEAD_AGENT_TOOLS
from .marketing_agent import MARKETING_AGENT_TOOLS
from .listing_agent import LISTING_AGENT_TOOLS
from .transaction_agent import TRANSACTION_AGENT_TOOLS
from .document_agent import DOCUMENT_AGENT_TOOLS
from .research_agent import RESEARCH_AGENT_TOOLS


# ─── Intent Keywords ─────────────────────────────────────────────────────────

_INTENT_PATTERNS = {
    "lead": [
        r"\blead[s]?\b", r"\bqualif", r"\bpipeline\b", r"\bscore[s]?\b",
        r"\brecommend\b.*\blead\b", r"\bfollow.up\b", r"\bhot\b.*\blead\b",
        r"\bwho should\b", r"\bcall today\b",
    ],
    "marketing": [
        r"\bmarket\b.*\bcampaign\b", r"\bsocial\b", r"\bpost\b", r"\binstagram\b",
        r"\bfacebook\b", r"\bnewsletter\b", r"\bcampaign\b", r"\bcontent\b",
        r"\bcreate.*post\b", r"\bannounce\b",
    ],
    "listing": [
        r"\bmls\b", r"\bdescript", r"\blisting\b", r"\bcompare\b.*\bpropert",
        r"\bprice\b.*\banalysis\b", r"\blist\b.*\bprice\b",
    ],
    "transaction": [
        r"\btransaction\b", r"\bdeadline\b", r"\bclosing\b", r"\bcontingenc",
        r"\binspection\b", r"\bfinancing\b", r"\bdue date\b", r"\btimeline\b",
    ],
    "document": [
        r"\bdocument\b", r"\bcontract\b", r"\bagreement\b", r"\bpdf\b",
        r"\bupload\b", r"\bclause\b", r"\bterms\b", r"\bsummarize.*contract\b",
        r"\bextract\b",
    ],
    "research": [
        r"\bmarket\b.*\btrend\b", r"\bneighborhood\b", r"\bcompare.*\bneighbo",
        r"\bmarket.*report\b", r"\bresearch\b", r"\barea\b.*\bprice\b",
        r"\bcompare\b.*\bto\b.*\b(?:st\.?\s*)?[A-Z]", r"\bcompare\s+\w+\s+(?:and|vs\.?|to)\s+\w+",
    ],
}


# ─── Classifier ──────────────────────────────────────────────────────────────

def classify_intent(message: str) -> str:
    """Classify a user message into an agent intent.
    
    Returns one of: lead, marketing, listing, transaction, document, research, general.
    """
    msg_lower = message.lower()

    for intent, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return intent

    return "general"


# ─── Agent Registry ──────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    "lead": {
        "name": "Lead Agent",
        "description": "Qualifies leads, scores prospects, recommends follow-up actions",
        "tools": LEAD_AGENT_TOOLS,
    },
    "marketing": {
        "name": "Marketing Agent",
        "description": "Creates campaigns, social posts, listing announcements",
        "tools": MARKETING_AGENT_TOOLS,
    },
    "listing": {
        "name": "Listing Agent",
        "description": "Generates MLS descriptions, compares properties, price analysis",
        "tools": LISTING_AGENT_TOOLS,
    },
    "transaction": {
        "name": "Transaction Agent",
        "description": "Tracks deadlines, contract conditions, closing timelines",
        "tools": TRANSACTION_AGENT_TOOLS,
    },
    "document": {
        "name": "Document Agent",
        "description": "Analyzes contracts, extracts terms, identifies risks",
        "tools": DOCUMENT_AGENT_TOOLS,
    },
    "research": {
        "name": "Research Agent",
        "description": "Market trends, neighborhood comparisons, pricing data",
        "tools": RESEARCH_AGENT_TOOLS,
    },
    "general": {
        "name": "General Assistant",
        "description": "General questions, CRM queries, business insights",
        "tools": [],  # Uses the default ALL_TOOLS from agent.py
    },
}


# ─── Routing ─────────────────────────────────────────────────────────────────

class SupervisorDecision:
    """The result of supervisor routing."""
    def __init__(self, intent: str, agent_info: dict, confidence: float = 0.9):
        self.intent = intent
        self.agent_name = agent_info["name"]
        self.agent_description = agent_info["description"]
        self.tools = agent_info["tools"]
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "agent": self.agent_name,
            "description": self.agent_description,
            "confidence": self.confidence,
            "tool_count": len(self.tools),
        }


def route(message: str) -> SupervisorDecision:
    """Route a message to the right specialist agent.
    
    Args:
        message: The user's message.
    
    Returns:
        SupervisorDecision with intent, agent info, and tools.
    """
    intent = classify_intent(message)
    agent_info = AGENT_REGISTRY.get(intent, AGENT_REGISTRY["general"])
    return SupervisorDecision(
        intent=intent,
        agent_info=agent_info,
        confidence=0.95 if intent != "general" else 0.7,
    )


def get_agent_tools(intent: str) -> list:
    """Get the tools for a specific agent intent."""
    info = AGENT_REGISTRY.get(intent, AGENT_REGISTRY["general"])
    return info["tools"]
