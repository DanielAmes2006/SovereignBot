import discord
from discord.ext import commands
from discord import app_commands
import json
import os

SERVER_INFO_FILE = "server_info.json"

def load_server_info():
    """ Loads server configuration from JSON file """
    if os.path.exists(SERVER_INFO_FILE):
        with open(SERVER_INFO_FILE, "r") as file:
            return json.load(file)
    return {}

def get_server_setting(guild_id, setting):
    """ Retrieves specific configuration setting for the guild """
    server_info = load_server_info()
    return server_info.get(str(guild_id), {}).get(setting, None)

class Fundamentals(commands.Cog):
    """ Handles essential bot permissions and admin utilities """

    def __init__(self, bot):
        self.bot = bot

    def has_mod_perms(self, ctx):
        """ Checks if user has mod permissions dynamically """
        mod_roles = get_server_setting(ctx.guild.id, "roles").get("mod_perms", [])
        return any(discord.utils.get(ctx.author.roles, name=role) for role in mod_roles) or ctx.author.guild_permissions.administrator

    def has_xp_perms(self, ctx):
        """ Checks if user has XP permissions dynamically """
        xp_roles = get_server_setting(ctx.guild.id, "roles").get("xp_perms", [])
        return any(discord.utils.get(ctx.author.roles, name=role) for role in xp_roles)

    @commands.command(name="update_tree")
    async def update_tree(self, ctx):
        """ Manually update the bot's command tree (Prefix Command) """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need **Administrator** permissions to update the command tree.")
            return

        await self.bot.tree.sync()
        await ctx.send("✅ **Slash commands have been manually updated!**")

    @app_commands.command(name="update_tree", description="Manually update the bot's command tree - Slash Command")
    async def update_tree_slash(self, interaction: discord.Interaction):
        """ Manually update the bot's command tree using a Slash Command """
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ You need **Administrator** permissions to update the command tree.", ephemeral=True)
            return

        await self.bot.tree.sync()
        await interaction.response.send_message("✅ **Slash commands have been manually updated!**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Fundamentals(bot))
