"""
RealtyAI Tools — LangChain @tool decorated functions the AI agent can call.

Now connected to real PostgreSQL database via db.py.
Falls back to mock data if database is unavailable.
"""
from typing import Optional
from datetime import datetime, timedelta
import uuid

from langchain_core.tools import tool

import logging
logger = logging.getLogger(__name__)

try:
    from db import (
        get_hot_leads_from_db, search_leads_in_db, get_lead_count_from_db,
        get_active_listings_from_db, search_properties_in_db,
    )
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    logger.warning(f"DB module unavailable, using mock data: {e}")


# ─── Mock Data (fallback when DB is unavailable) ────────────────────────────

_MOCK_LEADS = [
    {"id": str(uuid.uuid4()), "first_name": "John", "last_name": "Smith", "email": "john.smith@email.com",
     "phone": "(555) 123-4567", "source": "zillow", "status": "qualifying",
     "budget": 550000, "location_interest": "Windermere", "property_type_interest": "single_family",
     "timeline": "30_days", "pre_approved": True,
     "ai_score": 87, "ai_score_reason": "Pre-approved. Wants to buy within 30 days. Responds quickly.",
     "notes": "Viewed 123 Main St yesterday.",
     "last_contacted_at": (datetime.utcnow() - timedelta(days=1)).isoformat()},
    {"id": str(uuid.uuid4()), "first_name": "Sarah", "last_name": "Johnson", "email": "sarah.j@email.com",
     "phone": "(555) 987-6543", "source": "website", "status": "new",
     "budget": 350000, "location_interest": "Downtown", "property_type_interest": "condo",
     "timeline": "90_days", "pre_approved": False,
     "ai_score": 45, "ai_score_reason": "Early stage. No pre-approval. Longer timeline.",
     "notes": "", "last_contacted_at": None},
    {"id": str(uuid.uuid4()), "first_name": "Mike", "last_name": "Chen", "email": "mike.chen@email.com",
     "phone": "(555) 555-1234", "source": "redfin", "status": "qualified",
     "budget": 720000, "location_interest": "Summerside", "property_type_interest": "townhouse",
     "timeline": "immediate", "pre_approved": True,
     "ai_score": 92, "ai_score_reason": "Pre-approved. Ready to buy now. Cash buyer.",
     "notes": "Very responsive. Looking for 3+ beds.",
     "last_contacted_at": (datetime.utcnow() - timedelta(hours=6)).isoformat()},
    {"id": str(uuid.uuid4()), "first_name": "Emily", "last_name": "Davis", "email": "emily.d@email.com",
     "phone": "(555) 222-3333", "source": "referral", "status": "appointment_set",
     "budget": 850000, "location_interest": "Terwillegar", "property_type_interest": "single_family",
     "timeline": "60_days", "pre_approved": True,
     "ai_score": 78, "ai_score_reason": "Referred by past client. Pre-approved.",
     "notes": "Wants walkout basement.",
     "last_contacted_at": (datetime.utcnow() - timedelta(days=2)).isoformat()},
    {"id": str(uuid.uuid4()), "first_name": "Robert", "last_name": "Wilson", "email": "rwilson@email.com",
     "phone": "(555) 444-5555", "source": "open_house", "status": "contacted",
     "budget": 620000, "location_interest": "Westside", "property_type_interest": "single_family",
     "timeline": "45_days", "pre_approved": False,
     "ai_score": 55, "ai_score_reason": "Attended open house. Needs pre-approval.",
     "notes": "Has 2 kids, wants good school zone.",
     "last_contacted_at": (datetime.utcnow() - timedelta(days=7)).isoformat()},
]

_MOCK_PROPERTIES = [
    {"id": str(uuid.uuid4()), "address_street": "123 Main St", "address_city": "Edmonton",
     "address_state": "AB", "address_zip": "T5J 1A4", "property_type": "single_family",
     "beds": 4, "baths": 3, "sqft": 2400, "list_price": 525000, "status": "active",
     "description": "Beautifully renovated family home with modern kitchen and large backyard.",
     "features": ["Hardwood Floors", "Stainless Appliances"], "mls_number": "E1234567"},
    {"id": str(uuid.uuid4()), "address_street": "456 Oak Ave", "address_city": "Edmonton",
     "address_state": "AB", "address_zip": "T5K 2B5", "property_type": "condo",
     "beds": 2, "baths": 1, "sqft": 1100, "list_price": 275000, "status": "active",
     "description": "Stunning downtown condo with skyline views.",
     "features": ["In-suite Laundry", "Balcony"], "mls_number": "E1234568"},
    {"id": str(uuid.uuid4()), "address_street": "789 Pine Cres", "address_city": "Edmonton",
     "address_state": "AB", "address_zip": "T6W 3C4", "property_type": "townhouse",
     "beds": 3, "baths": 2.5, "sqft": 1650, "list_price": 389900, "status": "active",
     "description": "Modern townhouse in family-friendly Summerside.",
     "features": ["Attached Garage", "Vaulted Ceilings"], "mls_number": "E1234569"},
    {"id": str(uuid.uuid4()), "address_street": "321 Birch Blvd", "address_city": "Edmonton",
     "address_state": "AB", "address_zip": "T6R 4D5", "property_type": "single_family",
     "beds": 5, "baths": 4, "sqft": 3200, "list_price": 789900, "status": "active",
     "description": "Executive family home in prestigious Windermere.",
     "features": ["Gourmet Kitchen", "Walkout Basement", "3-Car Garage"], "mls_number": "E1234570"},
]


# ─── Tools ───────────────────────────────────────────────────────────────────

@tool
def get_hot_leads() -> list[dict]:
    """Top leads by AI score. Use for hot/best leads or who to call first."""
    try:
        if DB_AVAILABLE:
            db_leads = get_hot_leads_from_db()
            return [
                {"name": f"{l['first_name']} {l['last_name']}",
                 "budget": f"${l['budget']:,.0f}" if l.get("budget") else "unknown",
                 "timeline": l.get("timeline", "unknown"),
                 "score": l["ai_score"],
                 "reason": l.get("ai_score_reason", ""),
                 "id": l["id"]}
                for l in db_leads
            ]
    except Exception as e:
        logger.warning(f"get_hot_leads_from_db failed, falling back to mock: {e}")

    sorted_leads = sorted(_MOCK_LEADS, key=lambda l: l["ai_score"], reverse=True)
    return [
        {"name": f"{l['first_name']} {l['last_name']}",
         "budget": f"${l['budget']:,}" if l.get("budget") else "unknown",
         "timeline": l.get("timeline", "unknown"),
         "score": l["ai_score"],
         "reason": l.get("ai_score_reason", ""),
         "id": l["id"]}
        for l in sorted_leads
    ]


@tool
def search_leads(name: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    """Find leads by name or status.
    
    Args:
        name: Partial name (first or last).
        status: Lead status (new, qualifying, qualified, contacted, ...).
    """
    try:
        if DB_AVAILABLE:
            return search_leads_in_db(name=name, status=status)
    except Exception as e:
        logger.warning(f"search_leads_in_db failed, falling back to mock: {e}")

    results = _MOCK_LEADS
    if name:
        results = [l for l in results if name.lower() in l["first_name"].lower() or name.lower() in l["last_name"].lower()]
    if status:
        results = [l for l in results if l["status"] == status]
    return results


@tool
def get_lead_count() -> dict:
    """Lead total + count by status. Use for 'how many leads'."""
    try:
        if DB_AVAILABLE:
            return get_lead_count_from_db()
    except Exception as e:
        logger.warning(f"get_lead_count_from_db failed, falling back to mock: {e}")

    counts = {}
    for l in _MOCK_LEADS:
        counts[l["status"]] = counts.get(l["status"], 0) + 1
    return {"total": len(_MOCK_LEADS), "by_status": counts}


@tool
def get_active_listings() -> list[dict]:
    """All active listings. Use for 'what's for sale' / current listings."""
    try:
        if DB_AVAILABLE:
            return get_active_listings_from_db()
    except Exception as e:
        logger.warning(f"get_active_listings_from_db failed, falling back to mock: {e}")

    return [p for p in _MOCK_PROPERTIES if p["status"] == "active"]


@tool
def search_properties(city: Optional[str] = None, min_price: Optional[float] = None,
                      max_price: Optional[float] = None, beds: Optional[int] = None) -> list[dict]:
    """Filter listings by city, price range, or bedrooms.
    
    Args:
        city: City name.
        min_price: Minimum list price.
        max_price: Maximum list price.
        beds: Minimum bedrooms.
    """
    try:
        if DB_AVAILABLE:
            return search_properties_in_db(city=city, min_price=min_price, max_price=max_price, beds=beds)
    except Exception as e:
        logger.warning(f"search_properties_in_db failed, falling back to mock: {e}")

    results = [p for p in _MOCK_PROPERTIES if p["status"] == "active"]
    if city:
        results = [p for p in results if city.lower() in p["address_city"].lower()]
    if min_price:
        results = [p for p in results if p["list_price"] >= min_price]
    if max_price:
        results = [p for p in results if p["list_price"] <= max_price]
    if beds:
        results = [p for p in results if p["beds"] >= beds]
    return results


# ─── All tools list ─────────────────────────────────────────────────────────

ALL_TOOLS = [
    get_hot_leads,
    search_leads,
    get_lead_count,
    get_active_listings,
    search_properties,
]
