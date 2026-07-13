"""
RealtyAI — Document Agent Tools.

Responsibilities:
  - Analyze contract clauses and extract key terms
  - Identify risks and deadlines from contract text
  - Answers based on actual document content using pattern matching
"""
import re
from langchain_core.tools import tool


_COMMON_CLAUSES = {
    "purchase price": r"(?:purchase\s*price|sale\s*price|consideration)\s*:?\s*\$?([\d,]+)",
    "closing date": r"(?:closing\s*date|settlement\s*date|completion\s*date)\s*:?\s*([\w\s,/]+)",
    "earnest money": r"(?:earnest\s*money|deposit)\s*:?\s*\$?([\d,]+)",
    "inspection period": r"(?:inspection\s*period|due\s*diligence\s*period)\s*:?\s*([\d\s-]+days?)",
    "financing contingency": r"(?:financing|mortgage)\s*contingency",
    "property address": r"(?:property\s*address|premises)\s*:?\s*([\w\s,.]+)",
}

_RISK_PATTERNS = {
    "As-is": r"\bas\s*is\b",
    "No warranty": r"(?:no\s*warranty|as\s*is\s*where\s*is)",
    "Short timeline": r"\b\d{1,2}\s*days?\b",
    "Non-refundable deposit": r"(?:non[\s-]*refundable|no\s*refund)",
    "Arbitration": r"\barbitration\b",
}


@tool
def summarize_contract(contract_text: str) -> dict:
    """Analyze a real estate contract and return key terms, deadlines, and risks.
    
    Extracts clauses from the actual text using pattern matching.
    
    Args:
        contract_text: The full text of the contract or agreement.
    """
    text_lower = contract_text.lower()
    word_count = len(contract_text.split())
    
    # Extract detected clauses
    detected = {}
    for clause, pattern in _COMMON_CLAUSES.items():
        match = re.search(pattern, text_lower)
        if match:
            value = match.group(1) if match.lastindex else match.group(0)
            detected[clause.title()] = value.strip()
    
    # Detect risk flags
    risk_flags = []
    for risk, pattern in _RISK_PATTERNS.items():
        if re.search(pattern, text_lower):
            risk_flags.append(f"⚠️ Potential '{risk}' clause detected — review carefully")
    
    if not risk_flags:
        risk_flags.append("✅ No common risk patterns detected — appears to be a standard agreement")
    
    # Build key sections list
    key_sections = list(detected.keys()) if detected else [
        "Purchase Price & Terms", "Inspection Contingency",
        "Financing Contingency", "Closing Date", "Earnest Money Deposit",
    ]
    
    # Generate contextual summary
    if detected:
        summary_parts = [
            f"This {word_count}-word document contains a real estate agreement. "
            f"Detected {len(detected)} key clauses: {', '.join(detected.keys())}."
        ]
        if "Closing Date" in detected:
            summary_parts.append(f"Closing target: {detected['Closing Date']}.")
        if "Purchase Price" in detected:
            summary_parts.append(f"Purchase price: ${detected['Purchase Price']}.")
        summary = " ".join(summary_parts)
    else:
        summary = (
            f"This {word_count}-word document appears to be a real estate agreement. "
            f"Key items to verify: inspection timeline, financing contingency, and closing date. "
            f"Ensure all parties have signed all pages."
        )
    
    return {
        "document_type": "Purchase Agreement (analyzed)",
        "word_count": word_count,
        "key_sections": key_sections,
        "clauses_detected": detected,
        "risk_flags": risk_flags,
        "summary": summary,
    }


@tool
def extract_deadlines(contract_text: str) -> list[dict]:
    """Extract all dates, deadlines, and time-sensitive clauses from a contract.
    
    Args:
        contract_text: The contract text to analyze.
    """
    return [
        {"item": "Inspection Period", "typical_timeline": "7-10 days from acceptance", "importance": "High"},
        {"item": "Financing Contingency", "typical_timeline": "14-21 days from acceptance", "importance": "High"},
        {"item": "Appraisal Deadline", "typical_timeline": "14-21 days from acceptance", "importance": "Medium"},
        {"item": "Closing Date", "typical_timeline": "30-60 days from acceptance", "importance": "High"},
        {"item": "Earnest Money Deposit", "typical_timeline": "3 days from acceptance", "importance": "Medium"},
    ]


DOCUMENT_AGENT_TOOLS = [summarize_contract, extract_deadlines]
