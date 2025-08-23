import sqlite3
import os
from contextlib import closing

DB_FILE = os.getenv("CACHE_DB_FILE", "cache.db")

# Ensure table exists
def init_db():
    with closing(sqlite3.connect(DB_FILE)) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS roblox_cache (
                discord_id INTEGER PRIMARY KEY,
                roblox_id INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

def get_cached_roblox_id(discord_id: int):
    with closing(sqlite3.connect(DB_FILE)) as db:
        cursor = db.execute("SELECT roblox_id FROM roblox_cache WHERE discord_id = ?", (discord_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_cached_roblox_id(discord_id: int, roblox_id: int):
    with closing(sqlite3.connect(DB_FILE)) as db:
        db.execute("""
            INSERT INTO roblox_cache (discord_id, roblox_id)
            VALUES (?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET 
                roblox_id = excluded.roblox_id,
                updated_at = CURRENT_TIMESTAMP
        """, (discord_id, roblox_id))
        db.commit()

# Call once at startup
init_db()
