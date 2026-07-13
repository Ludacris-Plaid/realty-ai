"""
RealtyAI — Listing Agent Tools.

Responsibilities:
  - Generate MLS descriptions
  - Compare listings
  - Price analysis
"""
from datetime import datetime
from langchain_core.tools import tool

from tools import search_properties, get_active_listings


@tool
def generate_mls_description(address: str) -> dict:
    """Generate a professional MLS listing description for a property.
    
    Args:
        address: Street address of the property.
    """
    listings = get_active_listings.invoke({})
    prop = None
    for p in listings:
        if address.lower() in p.get("address_street", "").lower():
            prop = p
            break
    if not prop:
        return {"error": f"Property '{address}' not found"}

    beds = prop.get("beds", 0)
    baths = prop.get("baths", 0)
    sqft = prop.get("sqft", 0)
    price = prop.get("list_price", 0)
    desc = prop.get("description", "")

    mls = (
        f"**{beds}-Bedroom {prop.get('property_type', 'Home').replace('_', ' ').title()} in {prop['address_city']}**\n\n"
        f"{prop['address_street']}, {prop['address_city']}, {prop['address_state']} {prop['address_zip']}\n\n"
        f"${price:,} | {beds} beds | {baths} baths | {sqft:,} sqft\n\n"
        f"{desc}\n\n"
        f"**Highlights:**\n"
        f"• Spacious {beds}-bedroom layout perfect for families\n"
        f"• Modern finishes throughout\n"
        f"• Prime {prop['address_city']} location\n"
        f"• {sqft:,} square feet of living space\n\n"
        f"**Contact for a private showing today!**"
    )

    return {"mls_description": mls, "property": address}


@tool
def compare_properties(address1: str, address2: str) -> dict:
    """Compare two property listings side by side.
    
    Args:
        address1: First property address.
        address2: Second property address.
    """
    listings = get_active_listings.invoke({})
    p1 = p2 = None
    for p in listings:
        if address1.lower() in p.get("address_street", "").lower():
            p1 = p
        if address2.lower() in p.get("address_street", "").lower():
            p2 = p
    if not p1:
        return {"error": f"Property '{address1}' not found"}
    if not p2:
        return {"error": f"Property '{address2}' not found"}

    return {
        "property_1": {
            "address": p1["address_street"],
            "price": p1.get("list_price"),
            "beds": p1.get("beds"),
            "baths": p1.get("baths"),
            "sqft": p1.get("sqft"),
            "type": p1.get("property_type"),
        },
        "property_2": {
            "address": p2["address_street"],
            "price": p2.get("list_price"),
            "beds": p2.get("beds"),
            "baths": p2.get("baths"),
            "sqft": p2.get("sqft"),
            "type": p2.get("property_type"),
        },
    }


LISTING_AGENT_TOOLS = [generate_mls_description, compare_properties]
