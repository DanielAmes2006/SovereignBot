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

class ServerInfo(commands.Cog):
    """ Displays server configuration details """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="server_info")
    async def server_info(self, ctx):
        """ Displays the server's full name, abbreviation, and key settings (Prefix Command) """
        guild_id = ctx.guild.id
        server_name = get_server_setting(guild_id, "server_name")
        abbreviation = get_server_setting(guild_id, "abbreviation")
        channels = get_server_setting(guild_id, "channels")
        roles = get_server_setting(guild_id, "roles")

        if not server_name:
            await ctx.send("⚠️ Server information not found in the configuration file.")
            return

        embed = discord.Embed(title=f"{server_name} ({abbreviation})", color=discord.Color.blue())
        embed.add_field(name="🔗 Server ID", value=f"`{guild_id}`", inline=False)
        
        if channels:
            embed.add_field(name="📢 Channels", value="\n".join([f"**{name}:** `{id}`" for name, id in channels.items()]), inline=False)

        if roles:
            embed.add_field(name="🎭 Roles", value="\n".join([f"**{name}:** `{role}`" for name, role in roles.items()]), inline=False)

        await ctx.send(embed=embed)

    @app_commands.command(name="server_info", description="Displays server configuration details")
    async def server_info_slash(self, interaction: discord.Interaction):
        """ Calls the original server_info command via slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.server_info)
        await interaction.response.send_message("✅ Server info requested!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
