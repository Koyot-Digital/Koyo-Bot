import aiosqlite
import os

DB_FILE = os.getenv("CACHE_DB_FILE", "cache.db")
_db: aiosqlite.Connection | None = None

async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_FILE)
        await _db.execute("""
            CREATE TABLE IF NOT EXISTS roblox_cache (
                discord_id INTEGER PRIMARY KEY,
                roblox_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await _db.commit()
    return _db

async def get_cached_roblox_id(discord_id: int):
    db = await get_db()
    async with db.execute("SELECT roblox_id FROM roblox_cache WHERE discord_id = ?", (discord_id,)) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_cached_roblox_id(discord_id: int, roblox_id: int):
    db = await get_db()
    await db.execute("""
        INSERT INTO roblox_cache (discord_id, roblox_id)
        VALUES (?, ?)
        ON CONFLICT(discord_id) DO UPDATE SET roblox_id=excluded.roblox_id, updated_at=CURRENT_TIMESTAMP
    """, (discord_id, roblox_id))
    await db.commit()

async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
