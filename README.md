# Oakridge Role Updater Discord Bot (Serverless-Ready)

A Discord bot that automatically updates user roles based on Roblox points using **Bloxlink** and **Roblox DataStores**. The bot is designed to run **both as a traditional Discord bot or as a Flask-based serverless service**.

---

## Features

- Fetches Roblox IDs from Bloxlink for Discord users.
- Reads points from Roblox DataStores (Site Operator & Security points).
- Automatically assigns/removes Discord roles based on point thresholds.
- Optional caching of Roblox IDs for faster lookups.
- Slash command `/update` to manually trigger role updates.
- Modular design using Discord.py cogs.
- **Flask-based endpoint** for serverless deployment:
  - Can handle Discord interactions via HTTP requests.
  - Supports ephemeral responses and embeds.
  - Compatible with serverless platforms like AWS Lambda, Cloud Run, or Azure Functions.
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
- `PUBLIC_KEY= Discord Bot Public Key`
- `APP_ID= Discord Bot App Id`
- `BLOXLINK_API_KEY=Bloxlink Api Key`
- `ROBLOX_API_KEY=Roblox Api Key`

###  Roblox Api Key
The Roblox Open Cloud API Key must include the following permissions:
- API System: universe-datastores
- Operations: universe-datastores.objects:read

This ensures the bot can safely fetch player points from your game’s DataStore.