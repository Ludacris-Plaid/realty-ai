"""
RealtyAI — Research Agent Tools.

Responsibilities:
  - Market trends from DB listing data
  - Neighborhood comparisons (by city filter)
  - Price per square foot analytics
"""
from langchain_core.tools import tool

try:
    from db import get_active_listings_from_db
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


def _get_db_listings() -> list[dict]:
    """Fetch active listings from DB, returns empty list on failure."""
    if not DB_AVAILABLE:
        return []
    try:
        return get_active_listings_from_db()
    except Exception:
        return []


@tool
def market_snapshot(city: str = "", province: str = "") -> dict:
    """Get a market snapshot for a city: trends, median prices, days on market.
    
    Uses real DB data when available.
    
    Args:
        city: City name to filter by (leave empty for all).
        province: Province or state code (optional).
    """
    listings = _get_db_listings()
    
    # Filter by city if specified
    if city:
        filtered = [p for p in listings if city.lower() in p.get("address_city", "").lower()]
    else:
        filtered = list(listings)
    
    if filtered:
        prices = [p.get("list_price", 0) for p in filtered if p.get("list_price")]
        sqfts = [p.get("sqft", 0) for p in filtered if p.get("sqft")]
        
        sorted_prices = sorted(prices)
        median_price = sorted_prices[len(sorted_prices) // 2] if sorted_prices else 0
        avg_ppsf = sum(p / s for p, s in zip(prices, sqfts) if s > 0) / len([s for s in sqfts if s > 0]) if sqfts else 0
        cities_found = set(p.get("address_city", "") for p in filtered)
        total_value = sum(prices)
        
        return {
            "location": city or f"All ({len(cities_found)} cities)",
            "total_listings": len(filtered),
            "price_range": f"${min(prices):,.0f} — ${max(prices):,.0f}" if prices else "N/A",
            "median_price": median_price,
            "avg_price_per_sqft": round(avg_ppsf, 2),
            "total_market_value": f"${total_value:,.0f}",
            "cities_found": list(cities_found),
            "data_source": "Your realty database",
        }
    
    # Fallback: return a helpful message
    return {
        "location": city or "No listings in database",
        "total_listings": 0,
        "note": f"No active listings found{f' in {city}' if city else ''}. Seed the database to see market data.",
        "data_source": "Database query",
    }


@tool
def compare_neighborhoods(neighborhood_1: str, neighborhood_2: str,
                          city: str = "") -> dict:
    """Compare two neighborhoods across key real estate metrics using DB data.
    
    Args:
        neighborhood_1: First neighborhood name.
        neighborhood_2: Second neighborhood name.
        city: City filter (optional).
    """
    listings = _get_db_listings()
    
    def _get_neighborhood_stats(nb_name: str) -> dict:
        """Get stats for a neighborhood from DB listings."""
        # Match by address (neighborhood names often appear in street/city)
        nb_listings = [
            p for p in listings
            if nb_name.lower() in p.get("address_street", "").lower()
            or nb_name.lower() in p.get("address_city", "").lower()
            or nb_name.lower() in p.get("description", "").lower()
        ]
        if city:
            nb_listings = [p for p in nb_listings if city.lower() in p.get("address_city", "").lower()]
        
        if nb_listings:
            prices = [p.get("list_price", 0) for p in nb_listings if p.get("list_price")]
            beds = [p.get("beds", 0) for p in nb_listings if p.get("beds")]
            baths = [p.get("baths", 0) for p in nb_listings]
            sqfts = [p.get("sqft", 0) for p in nb_listings if p.get("sqft")]
            
            return {
                "listings_found": len(nb_listings),
                "avg_price": round(sum(prices) / len(prices)) if prices else 0,
                "price_range": f"${min(prices):,.0f} — ${max(prices):,.0f}" if prices else "N/A",
                "avg_beds": round(sum(beds) / len(beds), 1) if beds else 0,
                "avg_baths": round(sum(baths) / len(baths), 1) if baths else 0,
                "avg_sqft": round(sum(sqfts) / len(sqfts)) if sqfts else 0,
                "avg_ppsf": round(sum(p / s for p, s in zip(prices, sqfts) if s > 0) / max(len([x for x in sqfts if x > 0]), 1), 2) if sqfts and prices else 0,
            }
        return {"listings_found": 0, "avg_price": 0, "avg_sqft": 0, "avg_ppsf": 0}
    
    stats_1 = _get_neighborhood_stats(neighborhood_1)
    stats_2 = _get_neighborhood_stats(neighborhood_2)
    
    # Build comparison table
    comparison = [
        {"metric": "Active Listings",
         neighborhood_1: str(stats_1["listings_found"]),
         neighborhood_2: str(stats_2["listings_found"])},
        {"metric": "Average Price",
         neighborhood_1: f"${stats_1['avg_price']:,.0f}" if stats_1['avg_price'] else "N/A",
         neighborhood_2: f"${stats_2['avg_price']:,.0f}" if stats_2['avg_price'] else "N/A"},
        {"metric": "Avg Price/Sqft",
         neighborhood_1: f"${stats_1['avg_ppsf']:.0f}" if stats_1['avg_ppsf'] else "N/A",
         neighborhood_2: f"${stats_2['avg_ppsf']:.0f}" if stats_2['avg_ppsf'] else "N/A"},
        {"metric": "Avg Bedrooms",
         neighborhood_1: str(stats_1['avg_beds']),
         neighborhood_2: str(stats_2['avg_beds'])},
        {"metric": "Avg Bathrooms",
         neighborhood_1: str(stats_1['avg_baths']),
         neighborhood_2: str(stats_2['avg_baths'])},
        {"metric": "Avg Sq Ft",
         neighborhood_1: f"{stats_1['avg_sqft']:,.0f}" if stats_1['avg_sqft'] else "N/A",
         neighborhood_2: f"{stats_2['avg_sqft']:,.0f}" if stats_2['avg_sqft'] else "N/A"},
    ]
    
    # Verdict
    if stats_1['avg_price'] and stats_2['avg_price']:
        diff_pct = ((stats_2['avg_price'] - stats_1['avg_price']) / stats_1['avg_price']) * 100
        if abs(diff_pct) < 5:
            verdict = f"{neighborhood_1} and {neighborhood_2} are similarly priced (within {abs(diff_pct):.1f}%)."
        elif diff_pct > 0:
            verdict = f"{neighborhood_2} commands a {diff_pct:.0f}% premium over {neighborhood_1}."
        else:
            verdict = f"{neighborhood_1} is {abs(diff_pct):.0f}% more expensive than {neighborhood_2}."
    else:
        verdict = f"Insufficient data to compare {neighborhood_1} vs {neighborhood_2}. Try broader neighborhood names."
    
    return {
        "city": city or "All",
        "data_source": "Your realty database (active listings)",
        "comparison": comparison,
        "verdict": verdict,
    }


RESEARCH_AGENT_TOOLS = [market_snapshot, compare_neighborhoods]
