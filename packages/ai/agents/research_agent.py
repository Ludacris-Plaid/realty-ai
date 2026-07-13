"""
RealtyAI — Research Agent Tools.

Responsibilities:
  - Market trends and analysis
  - Neighborhood comparisons
  - Price per square foot data
  - Demographic insights

In MVP mode, returns mock market data.
In production, connects to MLS / market data APIs.
"""
from langchain_core.tools import tool


@tool
def market_snapshot(city: str = "Edmonton", province: str = "AB") -> dict:
    """Get a market snapshot for a city: trends, median prices, days on market.
    
    Args:
        city: City name.
        province: Province or state code.
    """
    # Mock data — in production, hit MLS API or local market data
    return {
        "location": f"{city}, {province}",
        "median_price": 425000,
        "price_change_3mo": "+2.3%",
        "price_change_12mo": "+5.1%",
        "avg_days_on_market": 34,
        "inventory_months": 3.2,
        "market_type": "Seller's Market" if 3.2 < 4 else "Balanced Market",
        "total_listings": 1842,
        "avg_price_per_sqft": 352,
        "note": "Mock data — connect MLS API for live figures",
    }


@tool
def compare_neighborhoods(neighborhood_1: str, neighborhood_2: str,
                          city: str = "Edmonton") -> dict:
    """Compare two neighborhoods across key real estate metrics.
    
    Args:
        neighborhood_1: First neighborhood name.
        neighborhood_2: Second neighborhood name.
        city: City containing both neighborhoods.
    """
    # Mock comparison data
    return {
        "city": city,
        "comparison": [
            {"metric": "Median Price", f"{neighborhood_1}": "$485,000", f"{neighborhood_2}": "$520,000"},
            {"metric": "Avg Price/Sqft", f"{neighborhood_1}": "$368", f"{neighborhood_2}": "$395"},
            {"metric": "Avg Days on Market", f"{neighborhood_1}": "28", f"{neighborhood_2}": "32"},
            {"metric": "School Rating", f"{neighborhood_1}": "7.5/10", f"{neighborhood_2}": "8.2/10"},
            {"metric": "Walk Score", f"{neighborhood_1}": "65", f"{neighborhood_2}": "72"},
            {"metric": "Crime Rate (per 100k)", f"{neighborhood_1}": "3,200", f"{neighborhood_2}": "2,800"},
        ],
        "verdict": f"{neighborhood_2} commands a premium due to better schools and walkability, but {neighborhood_1} offers better value per square foot.",
    }


RESEARCH_AGENT_TOOLS = [market_snapshot, compare_neighborhoods]
