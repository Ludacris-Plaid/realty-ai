"""
RealtyAI — Database Initializer.

Creates all required tables. No fake/demo data.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid


def init_db(db_url: str = "") -> str:
    """Create all database tables if they don't exist."""
    if not db_url:
        db_url = os.environ.get("DATABASE_URL", "")
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")

    engine = create_engine(db_url)

    from base import Base
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id UUID PRIMARY KEY, name TEXT NOT NULL,
                user_id UUID, audience TEXT DEFAULT '', status TEXT DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS showings (
                id UUID PRIMARY KEY, lead_name TEXT NOT NULL,
                user_id UUID, property_address TEXT, showing_time TEXT, status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS activities (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL,
                user_id UUID NOT NULL,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                intent TEXT DEFAULT 'general',
                model_used TEXT DEFAULT 'fast-model',
                status TEXT DEFAULT 'success',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS approvals (
                id UUID PRIMARY KEY,
                action_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                details JSONB DEFAULT '{}',
                agent_name TEXT DEFAULT 'General Assistant',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ,
                reviewed_by TEXT,
                notes TEXT
            )
        """))
        conn.commit()

    return db_url


if __name__ == "__main__":
    url = init_db()
    print(f"Database initialized: {url.split('@')[1].split('/')[0] if '@' in url else 'ok'}")
