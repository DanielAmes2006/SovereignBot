import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Define the file path for the XP data
XP_DATA_FILE = os.path.expanduser("~/SovereignBot/XP_data.json")

def load_xp_data():
    """Loads XP data from JSON file."""
    if os.path.exists(XP_DATA_FILE):
        with open(XP_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

def save_xp_data(data):
    """Saves updated XP data to JSON file."""
    with open(XP_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def get_server_setting(guild_id, setting, default=None):
    """ Safely retrieves a configuration setting for the guild """
    # Example for extensibility: Replace with actual server_info
    return default

class XPSystem(commands.Cog):
    """Handles XP tracking, role progression, and leaderboards."""
    def __init__(self, bot):
        self.bot = bot
        self.user_xp = load_xp_data()

    def has_xp_perms(self, ctx):
        """Checks if the user has XP permissions."""
        xp_roles = get_server_setting(ctx.guild.id, "roles", {}).get("xp_perms", [])
        return any(discord.utils.get(ctx.author.roles, name=role) for role in xp_roles)

    @commands.command()
    async def xp_add(self, ctx, amount: int, *users: discord.Member):
        """Adds XP to users (Requires XP Perms)."""
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        for user in users:
            user_id = str(user.id)
            if guild_id not in self.user_xp:
                self.user_xp[guild_id] = {}
            previous_xp = self.user_xp[guild_id].get(user_id, 0)
            self.user_xp[guild_id][user_id] = previous_xp + amount

        save_xp_data(self.user_xp)
        await ctx.send(f"✅ Added {amount} XP to the specified users!")

    @commands.command()
    async def xp_set(self, ctx, user: discord.Member, amount: int):
        """Sets XP for a user."""
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        user_id = str(user.id)
        if guild_id not in self.user_xp:
            self.user_xp[guild_id] = {}
        self.user_xp[guild_id][user_id] = max(0, amount)

        save_xp_data(self.user_xp)
        await ctx.send(f"✅ Set {user.display_name}'s XP to {amount}!")

    @commands.command()
    async def xp_view(self, ctx, user: discord.Member = None):
        """View XP of a user (Defaults to command sender)."""
        user = user or ctx.author
        guild_id = str(ctx.guild.id)
        xp = self.user_xp.get(guild_id, {}).get(str(user.id), 0)
        await ctx.send(f"{user.display_name} has {xp} XP!")

    @commands.command()
    async def leaderboard(self, ctx):
        """Displays XP leaderboard with pagination."""
        guild_id = str(ctx.guild.id)
        guild_xp = self.user_xp.get(guild_id, {})
        sorted_xp = sorted(guild_xp.items(), key=lambda x: x[1], reverse=True)

        leaderboard_entries = [
            f"{await self.bot.fetch_user(int(user_id))} - {xp} XP" 
            for user_id, xp in sorted_xp
        ]

        embed = discord.Embed(
            title="🏆 **Leaderboard**",
            description="\n".join(leaderboard_entries[:10]),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def xp_set_perms(self, ctx, *roles: discord.Role):
        """ Sets roles with XP permissions """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need **Administrator** permissions to use this command.")
            return
        
        server_info = load_xp_data()
        guild_id = str(ctx.guild.id)
        
        # Ensure the guild has data initialized
        if guild_id not in server_info:
            server_info[guild_id] = {"roles": {"xp_perms": []}}
        
        xp_roles = [role.name for role in roles]
        server_info[guild_id]["roles"]["xp_perms"] = xp_roles
        
        save_xp_data(server_info)
        await ctx.send(f"✅ Set XP Perms roles to: {', '.join(xp_roles)}")

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
