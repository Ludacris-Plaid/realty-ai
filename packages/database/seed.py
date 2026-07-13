"""
RealtyAI — Database Initializer & Seed Data.

Creates all tables and seeds demo data for the MVP.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

# Database URL (sync for init)
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://realty:realty_local_dev@localhost:5433/realty_ai"
).replace("+asyncpg", "").replace("+psycopg", "")

engine = create_engine(DB_URL, echo=True)


def create_tables():
    """Create all tables from SQLAlchemy models."""
    from src.base import Base
    from src.models import (
        User, AgentProfile, Client, Lead, Property,
        Document, Conversation, Message, AIMemory, Workflow, WorkflowStep
    )
    Base.metadata.create_all(engine)
    print("✓ All tables created.")


def seed_data():
    """Seed demo data for the MVP."""
    from src.models import (
        User, AgentProfile, Lead, Property,
        LeadStatus, LeadSource, PropertyStatus, PropertyType
    )

    with Session(engine) as session:
        # Check if already seeded
        existing = session.query(User).count()
        if existing > 0:
            print("✓ Data already seeded, skipping.")
            return

        # Create demo agent
        agent_id = uuid.uuid4()
        org_id = uuid.uuid4()
        agent = User(
            id=agent_id,
            brokerage_id=org_id,
            email="sarah@eliterealty.com",
            full_name="Sarah Chen",
            password_hash="seed-user-no-login",
            role="agent",
            created_at=datetime.utcnow(),
        )
        session.add(agent)

        profile = AgentProfile(
            id=uuid.uuid4(),
            user_id=agent_id,
            brokerage_name="Edmonton Elite Realty",
            brokerage_phone="(555) 123-4567",
            license_number="RE12345",
            created_at=datetime.utcnow(),
        )
        session.add(profile)

        # Create leads
        leads_data = [
            {
                "first_name": "John", "last_name": "Smith",
                "email": "john.smith@email.com", "phone": "(555) 123-4567",
                "source": LeadSource.ZILLOW, "status": LeadStatus.QUALIFYING,
                "budget": 550000, "location_interest": "Windermere",
                "property_type_interest": "single_family",
                "timeline": "30_days", "pre_approved": True,
                "ai_score": 87, "ai_score_reason": "Pre-approved. Active within 30 days. Responds quickly.",
                "notes": "Viewed 3 properties last week. Prefers newer builds.",
                "last_contacted_at": datetime.utcnow() - timedelta(days=1),
            },
            {
                "first_name": "Sarah", "last_name": "Johnson",
                "email": "sarah.j@email.com", "phone": "(555) 987-6543",
                "source": LeadSource.WEBSITE, "status": LeadStatus.NEW,
                "budget": 350000, "location_interest": "Downtown",
                "property_type_interest": "condo",
                "timeline": "90_days", "pre_approved": False,
                "ai_score": 45, "ai_score_reason": "Early stage. No pre-approval yet.",
            },
            {
                "first_name": "Mike", "last_name": "Chen",
                "email": "mike.chen@email.com", "phone": "(555) 555-1234",
                "source": LeadSource.REDFIN, "status": LeadStatus.QUALIFIED,
                "budget": 720000, "location_interest": "Summerside",
                "property_type_interest": "townhouse",
                "timeline": "immediate", "pre_approved": True,
                "ai_score": 92, "ai_score_reason": "Pre-approved. Cash buyer. Ready to close.",
                "notes": "Very responsive. Looking for 3+ beds. Already sold his previous home.",
                "last_contacted_at": datetime.utcnow() - timedelta(hours=6),
            },
            {
                "first_name": "Emily", "last_name": "Davis",
                "email": "emily.d@email.com", "phone": "(555) 222-3333",
                "source": LeadSource.REFERRAL, "status": LeadStatus.APPOINTMENT_SET,
                "budget": 850000, "location_interest": "Terwillegar",
                "property_type_interest": "single_family",
                "timeline": "60_days", "pre_approved": True,
                "ai_score": 78, "ai_score_reason": "Referred by past client. Pre-approved. Has specific requirements.",
                "notes": "Wants walkout basement. Showing scheduled Saturday 2PM.",
                "last_contacted_at": datetime.utcnow() - timedelta(days=2),
            },
            {
                "first_name": "Robert", "last_name": "Wilson",
                "email": "rwilson@email.com", "phone": "(555) 444-5555",
                "source": LeadSource.OPEN_HOUSE, "status": LeadStatus.CONTACTED,
                "budget": 620000, "location_interest": "Westside",
                "property_type_interest": "single_family",
                "timeline": "45_days", "pre_approved": False,
                "ai_score": 55, "ai_score_reason": "Attended open house. Needs pre-approval. Moderate interest.",
                "notes": "Met at 123 Main open house. Has 2 kids, wants good school zone.",
                "last_contacted_at": datetime.utcnow() - timedelta(days=7),
            },
        ]
        for ld in leads_data:
            lead = Lead(
                id=uuid.uuid4(),
                agent_id=agent_id,
                brokerage_id=org_id,
                **ld
            )
            session.add(lead)

        # Create properties
        props_data = [
            {
                "address_street": "123 Main St", "address_city": "Edmonton",
                "address_state": "AB", "address_zip": "T5J 1A4",
                "property_type": PropertyType.SINGLE_FAMILY, "status": PropertyStatus.ACTIVE,
                "beds": 4, "baths": 3, "sqft": 2400, "lot_size": 6000,
                "year_built": 2018, "garage_spaces": 2,
                "list_price": 525000, "description": "Beautifully renovated family home with modern kitchen, hardwood floors, and a private backyard oasis. Open concept main floor with natural light throughout.",
                "features": ["Hardwood Floors", "Stainless Appliances", "Granite Countertops", "Central AC", "Fenced Yard", "Deck"],
                "mls_number": "E1234567",
            },
            {
                "address_street": "456 Oak Ave", "address_city": "Edmonton",
                "address_state": "AB", "address_zip": "T5K 2B5",
                "property_type": PropertyType.CONDO, "status": PropertyStatus.ACTIVE,
                "beds": 2, "baths": 1, "sqft": 1100, "year_built": 2020,
                "list_price": 275000, "description": "Stunning downtown condo with panoramic skyline views. Floor-to-ceiling windows, modern finishes, and premium amenities including gym and rooftop patio.",
                "features": ["In-suite Laundry", "Underground Parking", "Balcony", "Fitness Center", "Concierge"],
                "mls_number": "E1234568",
            },
            {
                "address_street": "789 Pine Cres", "address_city": "Edmonton",
                "address_state": "AB", "address_zip": "T6W 3C4",
                "property_type": PropertyType.TOWNHOUSE, "status": PropertyStatus.ACTIVE,
                "beds": 3, "baths": 2.5, "sqft": 1650, "year_built": 2022,
                "garage_spaces": 1,
                "list_price": 389900, "description": "Modern townhouse in the family-friendly Summerside community. End unit with extra windows, upgraded kitchen, and low-maintenance yard.",
                "features": ["Attached Garage", "Vaulted Ceilings", "Air Conditioning", "Walking Trails Nearby", "Lake Access"],
                "mls_number": "E1234569",
            },
            {
                "address_street": "321 Birch Blvd", "address_city": "Edmonton",
                "address_state": "AB", "address_zip": "T6R 4D5",
                "property_type": PropertyType.SINGLE_FAMILY, "status": PropertyStatus.ACTIVE,
                "beds": 5, "baths": 4, "sqft": 3200, "lot_size": 8500,
                "year_built": 2015, "garage_spaces": 3,
                "list_price": 789900, "description": "Executive family home in prestigious Windermere. Gourmet kitchen, main-floor office, bonus room, and developed walkout basement with wet bar.",
                "features": ["Gourmet Kitchen", "Walkout Basement", "3-Car Garage", "Central Vacuum", "Heated Floors", "Wet Bar"],
                "mls_number": "E1234570",
            },
        ]
        for pd in props_data:
            prop = Property(
                id=uuid.uuid4(),
                agent_id=agent_id,
                brokerage_id=org_id,
                **pd
            )
            session.add(prop)

        session.commit()
        print(f"✓ Seeded: 1 agent, {len(leads_data)} leads, {len(props_data)} properties")


if __name__ == "__main__":
    create_tables()
    seed_data()
    print("✓ Database initialization complete.")
