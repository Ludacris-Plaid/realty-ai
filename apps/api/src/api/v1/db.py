import os
from sqlalchemy import create_engine

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://realty:realty_local_dev@localhost:5433/realty_ai"
).replace("+asyncpg", "").replace("+psycopg", "")

engine = create_engine(DB_URL, echo=False)
