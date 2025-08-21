# Oakridge Role Updater Discord Bot

A Discord bot that automatically updates user roles based on their Roblox points using Bloxlink and Roblox DataStores.

---

## Features

- Fetches Roblox IDs from Bloxlink for Discord users.
- Reads points from Roblox DataStores.
- Automatically assigns/removes Discord roles based on point thresholds.
- Optional caching of Roblox IDs for performance.
- Slash command `/update` to manually trigger role updates.
- Modular design using Discord.py cogs.

---

## Setup

### Requirements

- Python 3.11+
- `discord.py` (2.5+)
- `aiohttp`
- `aiosqlite`
- `python-dotenv`

Install dependencies:

```bash
pip install -r requirements.txt
```
### .env
- `DISCORD_TOKEN= Discord Bot Token`
- `DATASTORE= Game Datastore Name`
- `GUILD_ID= Discord Server Id`
- `ROBLOX_UNIVERSE_ID= Roblox Game Universe Id`
- `USE_CACHE= Whether To Use Cache(true or false)`
- `BLOXLINK_API_KEY=Bloxlink Api Key`
- `ROBLOX_API_KEY=Roblox Api Key`

###  Roblox Api Key
The Roblox Open Cloud API Key must include the following permissions:
- API System: universe-datastores
- Operations: universe-datastores.objects:read

This ensures the bot can safely fetch player points from your game’s DataStore.