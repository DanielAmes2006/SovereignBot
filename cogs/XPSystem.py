import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

SERVER_INFO_FILE = os.path.join(os.path.dirname(__file__), "..", "server_info.json")

def load_server_info():
    """ Loads server configuration from JSON file """
    if os.path.exists(SERVER_INFO_FILE):
        with open(SERVER_INFO_FILE, "r") as file:
            return json.load(file)
    return {}

def get_server_setting(guild_id, setting, default=None):
    """ Safely retrieves a configuration setting for the guild """
    server_info = load_server_info()
    guild_data = server_info.get(str(guild_id), {})

    # Debugging: Print what’s actually being found
    print(f"🔍 Searching JSON for server {guild_id}")
    print(f"🔍 Retrieved Data: {guild_data}")

    return guild_data.get(setting, default)

def save_server_info(data):
    """ Saves updated server configuration to JSON file """
    with open(SERVER_INFO_FILE, "w") as file:
        json.dump(data, file, indent=4)

class XPSystem(commands.Cog):
    """ Handles XP tracking, role progression, and leaderboards """

    def __init__(self, bot):
        self.bot = bot
        self.user_xp = {}

    def has_xp_perms(self, ctx):
        """ Checks if the user has XP permissions """
        xp_roles = get_server_setting(ctx.guild.id, "roles")["xp_perms"]
        return any(discord.utils.get(ctx.author.roles, name=role) for role in xp_roles)

    @commands.command()
    async def xp_add(self, ctx, amount: int, *users: discord.Member):
        """ Adds XP to users (Requires XP Perms) """
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        for user in users:
            user_id = str(user.id)
            previous_xp = self.user_xp.get(user_id, 0)
            self.user_xp[user_id] = previous_xp + amount

            await self.update_roles(ctx, user, previous_xp)

        save_server_info(self.user_xp)
        await ctx.send(f"✅ Added {amount} XP to eligible users!")

    @app_commands.command(name="xp_add", description="Adds XP to specified users")
    async def xp_add_slash(self, interaction: discord.Interaction, amount: int, users: discord.Member):
        """ Calls xp_add via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.xp_add, amount, users)
        await interaction.response.send_message(f"✅ Added {amount} XP!", ephemeral=True)

    @commands.command()
    async def xp_view(self, ctx, user: discord.Member = None):
        """ View XP of a user (Defaults to command sender) """
        user = user or ctx.author
        xp = self.user_xp.get(str(user.id), 0)
        await ctx.send(f"{user.display_name} has {xp} XP!")

    @app_commands.command(name="xp_view", description="View XP of a user")
    async def xp_view_slash(self, interaction: discord.Interaction, user: discord.Member = None):
        """ Calls xp_view via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.xp_view, user)
        await interaction.response.send_message(f"✅ Viewing XP for {user.display_name}!", ephemeral=True)

    @commands.command()
    async def xp_set(self, ctx, user: discord.Member, amount: int):
        """ Set XP for a user """
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        user_id = str(user.id)
        previous_xp = self.user_xp.get(user_id, 0)
        self.user_xp[user_id] = max(0, amount)

        await self.update_roles(ctx, user, previous_xp)

        save_server_info(self.user_xp)
        await ctx.send(f"✅ Set {user.display_name}'s XP to {amount}!")

    @app_commands.command(name="xp_set", description="Set XP for a user")
    async def xp_set_slash(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """ Calls xp_set via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.xp_set, user, amount)
        await interaction.response.send_message(f"✅ Set XP for {user.display_name} to {amount}!", ephemeral=True)

    @commands.command()
    async def leaderboard(self, ctx):
        """ Displays XP leaderboard with pagination """
        sorted_xp = sorted(self.user_xp.items(), key=lambda x: x[1], reverse=True)
        leaderboard_entries = [f"{await self.bot.fetch_user(int(user_id))} - {xp} XP" for user_id, xp in sorted_xp]

        embed = discord.Embed(title="🏆 **Leaderboard**", description="\n".join(leaderboard_entries[:10]), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @app_commands.command(name="leaderboard", description="Displays XP leaderboard")
    async def leaderboard_slash(self, interaction: discord.Interaction):
        """ Calls leaderboard via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.leaderboard)
        await interaction.response.send_message("✅ Fetching leaderboard!", ephemeral=True)

    async def update_roles(self, ctx, user, previous_xp):
        """ Assigns roles strictly by progression, removes previous ranks, and ensures XP announcements """
        role_thresholds = get_server_setting(ctx.guild.id, "roles")["xp_roles"]
        user_id = str(user.id)
        current_xp = self.user_xp.get(user_id, 0)
        previous_role = None

        for role_name, required_xp in role_thresholds.items():
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role:
                if previous_xp < required_xp <= current_xp:
                    await user.add_roles(role)

                if previous_role:
                    old_role = discord.utils.get(ctx.guild.roles, name=previous_role)
                    if old_role and old_role in user.roles:
                        await user.remove_roles(old_role)

            previous_role = role_name

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
