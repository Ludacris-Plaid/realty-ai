"""
RealtyAI Scraper CLI — scrape real property data from Zillow.

Usage:
    python -m hermes.scraper.cli "Edmonton, AB" --count 30
    python -m hermes.scraper.cli "Calgary, AB" --count 20 --seed
"""

import json
import sys
import os


def main():
    """CLI entry point for the scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="RealtyAI Property Scraper")
    parser.add_argument("location", nargs="?", default="Edmonton, AB",
                       help="City/location to scrape (e.g. 'Edmonton, AB')")
    parser.add_argument("--count", "-c", type=int, default=25,
                       help="Maximum listings to scrape")
    parser.add_argument("--seed", "-s", action="store_true",
                       help="Seed results into the database after scraping")
    parser.add_argument("--db-url", help="Database URL (defaults to DATABASE_URL env var)")
    parser.add_argument("--json", action="store_true",
                       help="Output results as JSON")
    parser.add_argument("--no-fallback", action="store_true",
                       help="Don't use fallback data if scraping fails")

    args = parser.parse_args()

    if args.seed:
        from .pipeline import scrape_and_seed
        result = scrape_and_seed(
            location=args.location,
            count=args.count,
            db_url=args.db_url or "",
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n=== Scrape & Seed Complete ===")
            print(f"  Location:          {result['location']}")
            print(f"  Scraped:           {result['scraped']} listings")
            print(f"  Properties:        {result['properties_inserted']}")
            print(f"  Leads:             {result['leads_inserted']}")
            print(f"  Activities:        {result['activities_inserted']}")
            print(f"  Campaigns:         {result['campaigns_inserted']}")
            print(f"  Showings:          {result['showings_inserted']}")
            print(f"  Documents:         {result['documents_inserted']}")
            print(f"  Source:            {result['source']}")
    else:
        from .zillow import ZillowScraper
        scraper = ZillowScraper()
        listings = scraper.search(args.location, max_results=args.count)

        if not listings and args.no_fallback:
            print(f"No listings found for {args.location}")
            sys.exit(1)

        if args.json:
            print(json.dumps(listings, indent=2))
        else:
            print(f"\n=== Scraped {len(listings)} properties from {args.location} ===")
            print(f"  Source: {listings[0].get('source', 'unknown') if listings else 'none'}")
            for i, p in enumerate(listings[:5], 1):
                print(f"\n  {i}. {p['address_street']}, {p['address_city']}")
                print(f"     ${p['list_price']:,} | {p['beds']}bd/{p['baths']}ba/{p['sqft']}sqft")
                print(f"     Type: {p['property_type']} | Status: {p['status']}")
            if len(listings) > 5:
                print(f"\n  ... and {len(listings) - 5} more")


if __name__ == "__main__":
    main()