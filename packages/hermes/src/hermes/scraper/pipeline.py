import json
import logging
import uuid

from hermes.scraper.super_scraper import SuperScraper
from hermes.scraper.zillow import ZillowScraper

logger = logging.getLogger(__name__)


def scrape_and_seed(
    location: str = "Edmonton, AB",
    count: int = 25,
    db_url: str = "",
    user_id: str = "",
    max_price: int = None,
    min_beds: int = None,
    max_beds: int = None,
    min_baths: int = None,
    max_baths: int = None,
) -> dict:
    scraper = ZillowScraper(delay=0.5)
    items = scraper.search(location, count)

    if not items:
        return {"scraped": 0, "properties_inserted": 0, "location": location}

    # Apply price/bed/bath filters
    if max_price:
        items = [i for i in items if (i.get("list_price") or 0) <= max_price]
    if min_beds:
        items = [i for i in items if (i.get("beds") or 0) >= min_beds]
    if max_beds:
        items = [i for i in items if (i.get("beds") or 0) <= max_beds]
    if min_baths:
        items = [i for i in items if (i.get("baths") or 0) >= min_baths]
    if max_baths:
        items = [i for i in items if (i.get("baths") or 0) <= max_baths]

    if not db_url or not user_id:
        return {"scraped": len(items), "properties_inserted": 0, "location": location,
                "note": "No DB URL or user_id — properties listed but not stored"}

    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    aid = user_id
    inserted = 0

    with engine.connect() as conn:
        for item in items:
            pid = str(uuid.uuid4())
            features_json = json.dumps(item.get("features", []))
            images_json = json.dumps(item.get("images", []))
            try:
                sql = """
                    INSERT INTO properties (id, agent_id, address_street, address_city, address_state,
                        address_zip, list_price, beds, baths, sqft, property_type, status,
                        description, features, images, zillow_url,
                        created_at, updated_at)
                    VALUES (:id, :agent_id, :street, :city, :state, :zip, :price, :beds, :baths,
                        :sqft, :ptype, :status, :desc,
                        :features, :images, :zurl, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": pid, "agent_id": aid, "street": item["address_street"],
                    "city": item["address_city"],
                    "state": item["address_state"], "zip": item["address_zip"],
                    "price": item["list_price"], "beds": item["beds"], "baths": item["baths"],
                    "sqft": item["sqft"], "ptype": item["property_type"], "status": item["status"],
                    "desc": item["description"],
                    "features": features_json, "images": images_json,
                    "zurl": item.get("url", ""),
                })
                conn.commit()
                inserted += 1
            except Exception as e:
                logger.warning(f"Insert failed for {item.get('address_street','?')}: {e}")

    return {
        "status": "ok",
        "location": location,
        "scraped": len(items),
        "properties_inserted": inserted,
        "source": "zillow",
    }
