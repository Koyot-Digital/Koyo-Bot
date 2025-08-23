import os
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger("roblox")

UNIVERSE_ID = int(os.getenv("ROBLOX_UNIVERSE_ID"))
BLOXLINK_API_KEY = os.getenv("BLOXLINK_API_KEY")
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY")
GUILD_ID = int(os.getenv("GUILD_ID"))

def get_roblox_id(discord_id: int) -> Optional[int]:
    #Fetch Roblox ID from Bloxlink
    url = f"https://api.blox.link/v4/public/guilds/{GUILD_ID}/discord-to-roblox/{discord_id}"
    headers = {"Authorization": BLOXLINK_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Bloxlink request failed ({resp.status_code}) for Discord {discord_id}")
            return None
        data = resp.json()
        roblox_id = int(data.get("robloxID", 0))
        return roblox_id if roblox_id != 0 else None
    except requests.RequestException as e:
        logger.error(f"Bloxlink request error for Discord {discord_id}: {e}")
        return None


def get_points(roblox_id: int) -> Dict[str, int]:
    #Fetch points from Roblox DataStore
    url = f"https://apis.roblox.com/cloud/v2/universes/{UNIVERSE_ID}/data-stores/PlayerPoints/entries/{roblox_id}"
    headers = {"x-api-key": ROBLOX_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch points for Roblox {roblox_id} ({resp.status_code})")
            return {"SiteopPoints": 0, "SecurityPoints": 0}

        data = resp.json()
        return {
            "SiteopPoints": int(data.get("value", {}).get("SiteopPoints", 0)),
            "SecurityPoints": int(data.get("value", {}).get("SecurityPoints", 0)),
        }
    except requests.RequestException as e:
        logger.error(f"Roblox points request error for {roblox_id}: {e}")
    return {"SiteopPoints": 0, "SecurityPoints": 0}
