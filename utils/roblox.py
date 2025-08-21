import aiohttp
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger("roblox")

universe_id = int(os.getenv("ROBLOX_UNIVERSE_ID"))
BLOXLINK_API_KEY = os.getenv("BLOXLINK_API_KEY")
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Reusable session
_session: Optional[aiohttp.ClientSession] = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def get_roblox_id(discord_id: int) -> Optional[int]:
    #Get Roblox ID from Bloxlink API
    url = f"https://api.blox.link/v4/public/guilds/{GUILD_ID}/discord-to-roblox/{discord_id}"
    headers = {"Authorization": BLOXLINK_API_KEY}
    session = await get_session()

    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                logger.warning(f"Bloxlink request failed ({resp.status}) for Discord {discord_id}")
                return None
            data = await resp.json()
            roblox_id = int(data.get("robloxID", 0))
            return roblox_id if roblox_id != 0 else None
    except aiohttp.ClientError as e:
        logger.error(f"Bloxlink request error for Discord {discord_id}: {e}")
    except asyncio.TimeoutError:
        logger.warning(f"Bloxlink request timed out for Discord {discord_id}")
    return None


async def get_points(roblox_id: int) -> Dict[str, int]:
    #Fetch points from Roblox DataStore
    url = f"https://apis.roblox.com/cloud/v2/universes/{universe_id}/data-stores/PlayerPoints/entries/{roblox_id}"
    headers = {"x-api-key": ROBLOX_API_KEY}
    session = await get_session()

    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                logger.warning(f"Failed to fetch points for Roblox {roblox_id} ({resp.status})")
                return {"SiteopPoints": 0, "SecurityPoints": 0}
            data = await resp.json()
            return {
                "SiteopPoints": int(data.get("value", {}).get("SecurityPoints", 0)),
                "SecurityPoints": int(data.get("value", {}).get("SiteopPoints", 0))
            }
    except aiohttp.ClientError as e:
        logger.error(f"Roblox points request error for {roblox_id}: {e}")
    except asyncio.TimeoutError:
        logger.warning(f"Roblox points request timed out for {roblox_id}")

    return {"SiteopPoints": 0, "SecurityPoints": 0}


async def close_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
