import os
import psycopg
from psycopg_pool import ConnectionPool
from typing import AsyncGenerator

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/athena")
_pool: Optional[ConnectionPool] = None

def get_pool() -> ConnectionPool:
    global _pool
    if not _pool:
        _pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10)
    return _pool

async def ensure_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn

async def get_or_create_bot_config(bot_id: str):
    async with ensure_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO athena_bot_config (bot_id, config) VALUES (%s, %s) "
                "ON CONFLICT (bot_id) DO UPDATE SET bot_id = EXCLUDED.bot_id "
                "RETURNING config",
                (bot_id, "{}")
            )
            return await cur.fetchone()
