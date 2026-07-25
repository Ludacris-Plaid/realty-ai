"""
Scrape Pipeline — scrape property listings and insert into DB.

Only inserts real scraped properties. No fake lead generation.
"""
import uuid
import logging

logger = logging.getLogger(__name__)


def scrape_and_seed(location: str = "Edmonton, AB", count: int = 25, db_url: str = "", user_id: str = "") -> dict:
    """Scrape real listings and insert into properties table."""
    from sqlalchemy import create_engine

    if not db_url:
        import os
        db_url = os.getenv("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")

    engine = create_engine(db_url)

    from .zillow import ZillowScraper
    scraper = ZillowScraper(delay=0.5)
    listings = scraper.search(location, max_results=count)

    if not listings:
        logger.warning("No listings retrieved from scraper.")
        return {"location": location, "error": "no_listings", "properties_inserted": 0}

    inserted = _insert_properties(engine, listings, user_id)

    return {
        "location": location,
        "scraped": len(listings),
        "properties_inserted": inserted,
        "source": listings[0].get("source", "unknown") if listings else "none",
    }


def _insert_properties(engine, listings: list[dict], agent_id: str = "") -> int:
    """Insert scraped properties into the properties table."""
    import json
    aid = agent_id or str(uuid.uuid4())
    with engine.connect() as conn:
        count = 0
        for item in listings:
            try:
                pid = str(uuid.uuid4())
                features_json = json.dumps(item.get("features", []))
                meta = json.dumps({
                    "scraped_at": item.get("scraped_at", ""),
                    "source": item.get("source", "scraper"),
                    "features": item.get("features", []),
                })

                sql = """
                    INSERT INTO properties (id, agent_id, address_street, address_city, address_state,
                        address_zip, list_price, beds, baths, sqft, property_type, status,
                        year_built, lot_size, garage_spaces, description, features, metadata,
                        created_at, updated_at)
                    VALUES (:id, :agent_id, :street, :city, :state, :zip, :price, :beds, :baths,
                        :sqft, :ptype, :status, :year, :lot, :garage, :desc,
                        :features, :meta, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": pid, "agent_id": aid, "street": item["address_street"],
                    "city": item["address_city"],
                    "state": item["address_state"], "zip": item["address_zip"],
                    "price": item["list_price"], "beds": item["beds"], "baths": item["baths"],
                    "sqft": item["sqft"], "ptype": item["property_type"], "status": item["status"],
                    "year": item["year_built"], "lot": item["lot_size"],
                    "garage": item["garage_spaces"], "desc": item["description"],
                    "features": features_json, "meta": meta,
                })
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert property: {e}")
                continue

        conn.commit()
        logger.info(f"Inserted {count} properties")
        return count


from sqlalchemy import text  # noqa: E402
