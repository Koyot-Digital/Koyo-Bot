import discord
from discord.ext import commands
import os
import asyncio
import logging
from dotenv import load_dotenv
from utils import cache

# Load env
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=int(os.getenv("GUILD_ID"))))
        logger.info(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        logger.error("Failed to sync commands", exc_info=e)

    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                logger.info(f"Loaded cog: {file}")
            except Exception as e:
                logger.error(f"Failed to load cog {file}", exc_info=e)

async def main():
    await cache.get_db()
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
