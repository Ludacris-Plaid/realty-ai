"""
Scrape Pipeline — transforms scraped property data into DB records.

Strategy:
  1. Scrape listings from Zillow (or fallback)
  2. Insert properties into the `properties` table
  3. Generate realistic leads from property data
  4. Generate activities, campaigns, showings, and documents

Usage:
    from hermes.scraper import scrape_and_seed
    result = scrape_and_seed(location="Edmonton, AB", count=25)
"""

import uuid
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def scrape_and_seed(location: str = "Edmonton, AB", count: int = 25, db_url: str = "") -> dict:
    """Main entry point: scrape listings and seed the database.
    
    Returns a dict with counts of what was inserted.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    if not db_url:
        import os
        db_url = os.getenv("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")

    engine = create_engine(db_url)

    # Phase 1: Scrape
    from .zillow import ZillowScraper
    scraper = ZillowScraper(delay=0.5)
    listings = scraper.search(location, max_results=count)

    if not listings:
        logger.warning("No listings retrieved from scraper. Using fallback data.")
        from .zillow import ZillowScraper
        # ZillowScraper already falls back internally; force fallback
        fallback_scraper = ZillowScraper()
        listings = fallback_scraper._fallback_listings(location, count)
        # Mark source
        for l in listings:
            l["source"] = "generated"

    # Phase 2: Insert properties
    inserted_props = _insert_properties(engine, listings)

    # Phase 3: Generate & insert leads
    inserted_leads = _generate_leads(engine, inserted_props)

    # Phase 4: Generate activities
    inserted_activities = _generate_activities(engine, inserted_props, inserted_leads)

    # Phase 5: Generate campaigns
    inserted_campaigns = _generate_campaigns(engine, inserted_props)

    # Phase 6: Generate showings
    inserted_showings = _generate_showings(engine, inserted_leads, inserted_props)

    # Phase 7: Generate documents
    inserted_docs = _generate_documents(engine, inserted_props)

    return {
        "location": location,
        "scraped": len(listings),
        "properties_inserted": inserted_props,
        "leads_inserted": inserted_leads,
        "activities_inserted": inserted_activities,
        "campaigns_inserted": inserted_campaigns,
        "showings_inserted": inserted_showings,
        "documents_inserted": inserted_docs,
        "source": listings[0].get("source", "unknown") if listings else "none",
    }


def _insert_properties(engine, listings: list[dict]) -> int:
    """Insert scraped properties into the properties table."""
    with engine.connect() as conn:
        # Check if properties table exists and has data
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM properties")).scalar()
            if existing and existing > 0:
                logger.info(f"Properties table already has {existing} rows — skipping insert")
                return existing
        except Exception:
            pass  # Table may not exist

        count = 0
        for item in listings:
            try:
                pid = str(uuid.uuid4())
                features_json = json.dumps(item.get("features", []))
                images_json = json.dumps(item.get("images", []))
                meta = json.dumps({
                    "scraped_at": item.get("scraped_at", ""),
                    "source": item.get("source", "scraper"),
                    "features": item.get("features", []),
                })

                sql = """
                    INSERT INTO properties (id, address_street, address_city, address_state,
                        address_zip, list_price, beds, baths, sqft, property_type, status,
                        year_built, lot_size, garage_spaces, description, features, metadata,
                        created_at, updated_at)
                    VALUES (:id, :street, :city, :state, :zip, :price, :beds, :baths,
                        :sqft, :ptype, :status, :year, :lot, :garage, :desc,
                        :features, :meta, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": pid, "street": item["address_street"], "city": item["address_city"],
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


def _generate_leads(engine, property_count: int) -> int:
    """Generate realistic leads from property data."""
    first_names = ["James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "David",
                   "Linda", "William", "Elizabeth", "Richard", "Barbara", "Joseph", "Susan",
                   "Thomas", "Jessica", "Christopher", "Sarah", "Daniel", "Karen", "Matthew",
                   "Lisa", "Anthony", "Nancy", "Mark", "Betty", "Donald", "Margaret",
                   "Steven", "Sandra", "Andrew", "Ashley", "Paul", "Kimberly", "Joshua", "Emily",
                   "Kenneth", "Donna", "Kevin", "Michelle", "Brian", "Carol", "George", "Amanda",
                   "Timothy", "Melissa", "Ronald", "Deborah", "Jason", "Stephanie"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
                  "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
                  "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
                  "Wright", "Scott", "Torres", "Nguyen", "Hill", "Green", "Adams",
                  "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]
    sources = ["ZILLOW", "REALTOR", "WEBSITE", "REFERRAL", "REDFIN", "OPEN_HOUSE",
               "SOCIAL", "COLD_CALL", "EMAIL", "WALK_IN"]
    statuses = ["NEW", "QUALIFYING", "QUALIFIED", "CONTACTED", "APPOINTMENT_SET",
                "CLOSED_WON", "CLOSED_LOST", "DORMANT"]
    timelines = ["Immediate", "30 days", "60 days", "90 days", "Flexible"]
    property_types = ["Single Family", "Townhouse", "Condo", "Duplex", "Bungalow"]
    areas_calgary = ["Kensington", "Beltline", "Inglewood", "Marda Loop", "Crescent Heights",
                     "Bridgeland", "Mission", "Killarney", "Hillhurst", "Altadore",
                     "Garrison Woods", "Bankview", "Sunalta", "Mount Pleasant", "Tuxedo Park"]
    areas_edmonton = ["Windermere", "Ambleside", "Rutherford", "Keswick", "Laurier Heights",
                      "Glenora", "Strathcona", "Oliver", "Garneau", "Terwillegar",
                      "Summerside", "Walker Lakes", "Chappelle", "Ellerslie", "Heritage Valley"]

    with engine.connect() as conn:
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM leads")).scalar()
            if existing and existing > 0:
                logger.info(f"Leads table already has {existing} rows — skipping")
                return existing
        except Exception:
            pass

        target = max(property_count * 2, 25)
        count = 0
        used_pairs = set()

        for _ in range(target * 2):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            pair = (fn, ln)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            score = random.randint(20, 98)
            budget = random.choice([250000, 300000, 350000, 400000, 450000, 500000, 550000,
                                   600000, 650000, 700000, 750000, 800000, 900000, 1000000,
                                   1200000, 1500000])
            ptype = random.choice(property_types)
            pre_approved = score > 60 and random.random() < 0.6
            area = random.choice(areas_edmonton + areas_calgary)

            # Score reasons
            high_reasons = ["Cash buyer, pre-approved, immediate timeline",
                            "Pre-approved, past client referral, ready to close",
                            "Pre-approved, active within 30 days, responds quickly",
                            "Referred by past client, pre-approved, specific requirements"]
            mid_reasons = ["Attended open house, needs pre-approval",
                           "Website inquiry, researching options, moderate budget",
                           "Referred by past client, exploring options",
                           "Active on Zillow, contacted for more info"]
            low_reasons = ["Early stage, no pre-approval yet",
                           "Budget exploration, long timeline",
                           "Just starting search, initial consultation only"]

            if score >= 80:
                reason = random.choice(high_reasons)
            elif score >= 50:
                reason = random.choice(mid_reasons)
            else:
                reason = random.choice(low_reasons)

            status_weights = {"NEW": 25, "QUALIFYING": 20, "QUALIFIED": 18, "CONTACTED": 15,
                             "APPOINTMENT_SET": 8, "CLOSED_WON": 4, "CLOSED_LOST": 6, "DORMANT": 4}
            status = random.choices(list(status_weights.keys()), weights=list(status_weights.values()))[0]

            timeline = random.choice(["Immediate", "30 days", "60 days", "90 days", "Flexible"])
            source = random.choice(sources)

            notes_map = {
                "NEW": "New lead from " + source.lower() + ", needs initial contact",
                "QUALIFYING": "Active in search, needs follow-up",
                "QUALIFIED": "Qualified buyer, specific requirements noted",
                "CONTACTED": "Contact made, awaiting response",
                "APPOINTMENT_SET": "Showing scheduled",
                "CLOSED_WON": "Successfully closed",
                "CLOSED_LOST": "Lost to competitor or changed mind",
                "DORMANT": "No activity in 30+ days",
            }
            notes = notes_map.get(status, "In pipeline")

            try:
                lid = str(uuid.uuid4())
                sql = """
                    INSERT INTO leads (id, first_name, last_name, email, phone,
                        source, status, budget, location_interest, property_type_interest,
                        timeline, pre_approved, ai_score, ai_score_reason, notes,
                        created_at, updated_at)
                    VALUES (:id, :fn, :ln, :email, :phone, :source, :status,
                        :budget, :location, :ptype, :timeline, :pre, :score,
                        :reason, :notes, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": lid,
                    "fn": fn, "ln": ln,
                    "email": f"{fn.lower()}.{ln.lower()}@email.com",
                    "phone": f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}",
                    "source": source, "status": status,
                    "budget": budget, "location": area,
                    "ptype": ptype, "timeline": timeline,
                    "pre": pre_approved, "score": score,
                    "reason": reason, "notes": notes,
                })
                count += 1
            except Exception as e:
                logger.warning(f"Lead insert failed: {e}")
                continue

            if count >= target:
                break

        conn.commit()
        logger.info(f"Inserted {count} leads")
        return count


def _generate_activities(engine, prop_count: int, lead_count: int) -> int:
    """Generate realistic activity records."""
    actions = [
        "Analyzed lead pipeline", "Generated listing description", "Scheduled property showing",
        "Qualified new lead", "Sent marketing campaign", "Updated lead status",
        "Created market report", "Analyzed neighborhood comparison", "Reviewed contract terms",
        "Extracted contract deadlines", "Generated listing description",
        "Qualified lead with AI scoring", "Pipeline analysis completed",
        "Market snapshot generated", "New campaign launched",
        "Lead scoring completed", "Contract analysis finished",
    ]
    intents = ["lead_management", "listing_optimization", "pipeline_analysis",
               "market_research", "compliance_check", "campaign_management",
               "document_analysis", "showing_scheduling"]

    with engine.connect() as conn:
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM activities")).scalar()
            if existing and existing > 0:
                logger.info(f"Activities table already has {existing} rows — skipping")
                return existing
        except Exception:
            pass

        target = max(lead_count, 30)
        count = 0
        for _ in range(target):
            action = random.choice(actions)
            intent = random.choice(intents)
            days_ago = random.randint(0, 14)
            created = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

            try:
                aid = str(uuid.uuid4())
                meta = json.dumps({"generated": True, "action": action})
                sql = """
                    INSERT INTO activities (id, organization_id, user_id, agent_name,
                        action, intent, model_used, status, metadata, created_at)
                    VALUES (:id, '00000000-0000-0000-0000-000000000001',
                        '00000000-0000-0000-0000-000000000002', 'Athena',
                        :action, :intent, 'deepseek-v4-flash-free', 'success',
                        :meta, :created)
                """
                conn.execute(text(sql), {
                    "id": aid, "action": action, "intent": intent,
                    "meta": meta, "created": created,
                })
                count += 1
            except Exception:
                continue

        conn.commit()
        logger.info(f"Inserted {count} activities")
        return count


def _generate_campaigns(engine, prop_count: int) -> int:
    """Generate realistic marketing campaigns."""
    names = [
        "Summer Open House Series", "New Listings Alert", "Referral Request Campaign",
        "Market Report Q3", "Holiday Greeting Campaign", "First-Time Buyer Workshop",
        "Luxury Property Showcase", "Neighborhood Spotlight Series",
        "Seasonal Maintenance Tips", "Client Appreciation Event",
    ]
    types = ["email", "social", "newsletter", "email", "social", "email", "social", "newsletter", "email", "social"]

    with engine.connect() as conn:
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
            if existing and existing > 0:
                logger.info(f"Campaigns table already has {existing} rows — skipping")
                return existing
        except Exception:
            pass

        count = 0
        for i, name in enumerate(names):
            ctype = types[i % len(types)]
            status = random.choices(
                ["active", "active", "active", "draft", "scheduled", "completed", "paused"],
                weights=[4, 4, 4, 2, 2, 3, 1]
            )[0]
            # Backdate some campaigns
            days_ago = random.randint(0, 60)
            created = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

            try:
                cid = str(uuid.uuid4())
                audience = random.choice([
                    "All leads", "Hot leads only", "Past clients",
                    "First-time buyers", "Luxury buyers", "Investors",
                    "Open house attendees", "Social media followers",
                ])
                sql = """
                    INSERT INTO campaigns (id, name, audience, status, created_at)
                    VALUES (:id, :name, :audience, :status, :created)
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": cid, "name": name,
                    "audience": audience, "status": status,
                    "created": created,
                })
                count += 1
            except Exception:
                continue

        conn.commit()
        logger.info(f"Inserted {count} campaigns")
        return count


def _generate_showings(engine, lead_count: int, prop_count: int) -> int:
    """Generate realistic property showings."""
    try:
        with engine.connect() as conn:
            leads = conn.execute(
                text("SELECT id, first_name, last_name FROM leads ORDER BY RANDOM() LIMIT 10")
            ).fetchall()
            props = conn.execute(
                text("SELECT id, address_street, address_city FROM properties ORDER BY RANDOM() LIMIT 10")
            ).fetchall()
    except Exception:
        leads = []
        props = []

    if not leads or not props:
        logger.info("No leads or properties available for showings")
        return 0

    with engine.connect() as conn:
        try:
            existing = conn.execute(text("SELECT COUNT(*) FROM showings")).scalar()
            if existing and existing > 0:
                return existing
        except Exception:
            pass

        count = 0
        for i in range(min(len(leads), len(props), 8)):
            lead = leads[i]
            prop = props[i]
            days_ahead = random.randint(0, 14)
            showing_time = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d %I:%M %p")
            status = random.choices(["pending", "confirmed", "completed", "cancelled"], weights=[3, 4, 2, 1])[0]

            try:
                sid = str(uuid.uuid4())
                name = f"{lead[1]} {lead[2]}"
                address = f"{prop[1]}, {prop[2]}"
                sql = """
                    INSERT INTO showings (id, lead_name, property_address, showing_time, status, created_at)
                    VALUES (:id, :name, :addr, :time, :status, NOW())
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": sid, "name": name,
                    "addr": address, "time": showing_time,
                    "status": status,
                })
                count += 1
            except Exception:
                continue

        conn.commit()
        logger.info(f"Inserted {count} showings")
        return count


def _generate_documents(engine, prop_count: int) -> int:
    """Generate sample document records."""
    templates = [
        ("Listing Agreement", "agreement", "pdf"),
        ("Client Intake Form", "form", "pdf"),
        ("Property Disclosure", "disclosure", "pdf"),
        ("Market Analysis Report", "report", "pdf"),
        ("Offer to Purchase", "contract", "pdf"),
        ("Home Inspection Checklist", "checklist", "pdf"),
    ]

    with engine.connect() as conn:
        try:
            # Check if documents table exists
            tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'documents'")).fetchall()
            if not tables:
                logger.info("Documents table doesn't exist — skipping document generation")
                return 0
            existing = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar()
            if existing and existing > 0:
                return existing
        except Exception:
            return 0

        count = 0
        for name, category, ext in templates:
            days_ago = random.randint(0, 90)
            created = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
            filesize = random.randint(50000, 500000)

            try:
                did = str(uuid.uuid4())
                sql = """
                    INSERT INTO documents (id, name, category, file_type, file_size, uploaded_at)
                    VALUES (:id, :name, :cat, :ftype, :fsize, :created)
                    ON CONFLICT (id) DO NOTHING
                """
                conn.execute(text(sql), {
                    "id": did, "name": name,
                    "cat": category, "ftype": ext,
                    "fsize": filesize, "created": created,
                })
                count += 1
            except Exception:
                continue

        conn.commit()
        logger.info(f"Inserted {count} documents")
        return count


import json  # noqa: E402 — must be after the docstring