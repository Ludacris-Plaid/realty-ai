"""
RealtyAI — Marketing Agent Tools.

Responsibilities:
  - Generate social media posts
  - Create listing descriptions
  - Plan marketing campaigns
  - Newsletter content
"""
from datetime import datetime, timedelta
from langchain_core.tools import tool

from tools import get_active_listings


@tool
def create_listing_post(address: str) -> dict:
    """Create a ready-to-post social media announcement for a property listing.
    
    Args:
        address: Street address of the listing.
    """
    listings = get_active_listings.invoke({})
    prop = None
    for p in listings:
        if address.lower() in p.get("address_street", "").lower():
            prop = p
            break
    if not prop:
        return {"error": f"Listing at '{address}' not found"}

    price = f"${prop.get('list_price', 0):,}"
    beds = prop.get("beds", "?")
    baths = prop.get("baths", "?")
    desc = prop.get("description", "Beautiful home.")

    caption = (
        f"🏡 **Just Listed!**\n\n"
        f"{prop['address_street']}, {prop['address_city']}, {prop['address_state']}\n\n"
        f"✨ {beds} bed | {baths} bath | {price}\n\n"
        f"{desc}\n\n"
        f"📞 Schedule your private showing today!\n"
        f"#JustListed #RealEstate #{prop['address_city'].replace(' ', '')}RealEstate"
    )

    return {
        "platforms": ["Instagram", "Facebook", "Twitter"],
        "caption": caption,
        "hashtags": ["#JustListed", "#RealEstate", f"#{prop['address_city']}RealEstate"],
        "property": prop["address_street"],
    }


@tool
def campaign_plan(property_address: str) -> dict:
    """Create a 7-day marketing campaign plan for a property listing.
    
    Args:
        property_address: Street address of the listing.
    """
    listings = get_active_listings.invoke({})
    prop = None
    for p in listings:
        if property_address.lower() in p.get("address_street", "").lower():
            prop = p
            break
    if not prop:
        return {"error": f"Listing '{property_address}' not found"}

    price = prop.get("list_price", 0)
    days = [
        {"day": 1, "channel": "Instagram", "content": f"Photo carousel: exterior, kitchen, master bedroom — caption: 'Welcome to {prop['address_street']}!'"},
        {"day": 2, "channel": "Facebook", "content": f"Neighborhood highlight: schools, parks, transit near {prop['address_street']}"},
        {"day": 3, "channel": "Email", "content": f"Send to buyer leads: New listing alert — ${price:,}"},
        {"day": 4, "channel": "Instagram Stories", "content": "Virtual tour walkthrough video"},
        {"day": 5, "channel": "Twitter/LinkedIn", "content": f"Market insight: Why {prop['address_city']} is appreciating"},
        {"day": 6, "channel": "Facebook", "content": "Open house announcement + direction video"},
        {"day": 7, "channel": "Email", "content": "Follow-up: highlights from open house + similar listings"},
    ]
    return {"property": property_address, "campaign_duration": "7 days", "daily_plan": days}


MARKETING_AGENT_TOOLS = [create_listing_post, campaign_plan]
