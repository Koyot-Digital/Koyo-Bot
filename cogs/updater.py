import discord
from discord.ext import commands
from discord import app_commands
import os
import logging
from utils import roblox, cache

# Configure logger for this cog
logger = logging.getLogger("updater")
logger.setLevel(logging.INFO)  # Set to INFO in production

# Role hierarchy logic
def get_highest_role(category, points, roles_config):
    #Get the highest eligible role for a given category and points.
    eligible = [r for r in roles_config[category] if points >= r["points"]]
    if not eligible:
        return None
    return max(eligible, key=lambda r: r["points"])["role_id"]


class Updater(commands.Cog):
    #Cog responsible for updating user roles based on Roblox points.
    def __init__(self, bot, roles_config):
        self.bot = bot
        self.roles_config = roles_config

    @app_commands.command(
        name="update",
        description="Update your roles based on your Roblox points."
    )
    async def update_roles(self, interaction: discord.Interaction):
        member = interaction.user
        logger.info(f"[COMMAND] /updateroles requested by {member} ({member.id})")

        # Send initial response embed
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Updating Roles",
                description=f"Fetching Roblox data for {member.mention}...",
                color=discord.Color.blurple()
            ).set_footer(text="This may take a few seconds."),
            ephemeral=True
        )

        # --- STEP 1: Roblox ID lookup ---
        roblox_id = None
        if os.getenv("USE_CACHE", "false").lower() == "true":
            roblox_id = await cache.get_cached_roblox_id(member.id)
            if roblox_id:
                logger.debug(f"[CACHE HIT] {member.id} → Roblox {roblox_id}")

        if not roblox_id:
            logger.debug(f"[CACHE MISS] Fetching Roblox ID for {member.id} from Bloxlink")
            roblox_id = await roblox.get_roblox_id(member.id)
            if not roblox_id:
                logger.warning(f"[NO ACCOUNT] {member} has no linked Roblox account")
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="Update Failed",
                        description="Could not find a linked Roblox account.",
                        color=discord.Color.red()
                    )
                )
                return

            if os.getenv("USE_CACHE", "false").lower() == "true":
                await cache.set_cached_roblox_id(member.id, roblox_id)
                logger.debug(f"[CACHE SET] Saved Roblox ID {roblox_id} for {member.id}")

        # --- STEP 2: Fetch points ---
        points = await roblox.get_points(roblox_id)
        siteop_points = points.get("SiteopPoints", 0)
        security_points = points.get("SecurityPoints", 0)
        logger.debug(f"[POINTS] Roblox {roblox_id}: siteop={siteop_points}, security={security_points}")

        # --- STEP 3: Determine highest roles ---
        siteop_role = get_highest_role("siteop", siteop_points, self.roles_config)
        security_role = get_highest_role("security", security_points, self.roles_config)
        logger.debug(f"[ROLES ELIGIBLE] siteop={siteop_role}, security={security_role}")

        # Decide what to add/remove
        roles_to_keep, roles_to_add, roles_to_remove = [], [], []

        if siteop_role:
            if siteop_role not in [r.id for r in member.roles]:
                roles_to_add.append(siteop_role)
            roles_to_keep.append(siteop_role)

        if security_role:
            if security_role not in [r.id for r in member.roles]:
                roles_to_add.append(security_role)
            roles_to_keep.append(security_role)

        for category in self.roles_config:
            for role_cfg in self.roles_config[category]:
                r_id = role_cfg["role_id"]
                if r_id not in roles_to_keep and r_id in [r.id for r in member.roles]:
                    roles_to_remove.append(r_id)

        logger.debug(f"[ROLES CHANGE] Add={roles_to_add}, Remove={roles_to_remove}")

        # --- STEP 4: Apply changes ---
        guild = interaction.guild
        added, removed = [], []

        for r_id in roles_to_add:
            role = guild.get_role(r_id)
            if role:
                await member.add_roles(role)
                added.append(role.name)
                logger.info(f"[ROLE ADD] Added {role.name} to {member}")

        for r_id in roles_to_remove:
            role = guild.get_role(r_id)
            if role:
                await member.remove_roles(role)
                removed.append(role.name)
                logger.info(f"[ROLE REMOVE] Removed {role.name} from {member}")

        # --- STEP 5: Send final embed ---
        embed = discord.Embed(
            title="Roles Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="👷 Site Operator", value=f"`{siteop_points}` → {f'<@&{siteop_role}>' if siteop_role else 'None'}", inline=False)
        embed.add_field(name="🛡 Security", value=f"`{security_points}` → {f'<@&{security_role}>' if security_role else 'None'}", inline=False)
        embed.add_field(name="📥 Added", value=", ".join(added) if added else "None", inline=True)
        embed.add_field(name="📤 Removed", value=", ".join(removed) if removed else "None", inline=True)
        embed.set_footer(text=f"Requested by {member.display_name}")

        await interaction.edit_original_response(embed=embed)


async def setup(bot):
    import json
    with open("data/roles.json") as f:
        roles_config = json.load(f)

    await bot.add_cog(
        Updater(bot, roles_config),
        guild=discord.Object(id=int(os.getenv("GUILD_ID")))
    )

