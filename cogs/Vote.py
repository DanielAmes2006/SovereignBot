import discord
from discord.ext import commands
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

def save_server_info(data):
    """ Saves updated server configuration to JSON file """
    with open(SERVER_INFO_FILE, "w") as file:
        json.dump(data, file, indent=4)

class Vote(commands.Cog):
    """ Handles automated voting systems for forums """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """ Auto-reacts with 👍👎 when a thread is created in voting forums """
        voting_forums = get_server_setting(thread.guild.id, "voting_forums") or []
        
        if thread.parent.id not in voting_forums:
            return  # Exit if thread isn't in a voting forum

        async for starter_message in thread.history(limit=1, oldest_first=True):
            await starter_message.add_reaction('👍')
            await starter_message.add_reaction('👎')

    @commands.command()
    async def add_voting_forum(self, ctx, channel: discord.TextChannel):
        """ Adds a voting forum dynamically """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need Administrator permissions to modify voting forums.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        if guild_id not in server_info:
            server_info[guild_id] = {"voting_forums": []}

        voting_forums = server_info[guild_id].get("voting_forums", [])
        
        if channel.id in voting_forums:
            await ctx.send(f"⚠️ **{channel.name}** is already a voting forum.")
            return

        voting_forums.append(channel.id)
        server_info[guild_id]["voting_forums"] = voting_forums
        save_server_info(server_info)

        await ctx.send(f"✅ **{channel.name}** has been added as a voting forum!")

    @commands.command()
    async def remove_voting_forum(self, ctx, channel: discord.TextChannel):
        """ Removes a voting forum dynamically """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need Administrator permissions to modify voting forums.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        voting_forums = server_info[guild_id].get("voting_forums", [])

        if channel.id not in voting_forums:
            await ctx.send(f"⚠️ **{channel.name}** is not set as a voting forum.")
            return

        voting_forums.remove(channel.id)
        server_info[guild_id]["voting_forums"] = voting_forums
        save_server_info(server_info)

        await ctx.send(f"✅ **{channel.name}** has been removed from the voting forums.")

    @commands.command()
    async def list_voting_forums(self, ctx):
        """ Lists all active voting forums """
        guild_id = str(ctx.guild.id)
        voting_forums = get_server_setting(ctx.guild.id, "voting_forums") or []

        if not voting_forums:
            await ctx.send("⚠️ No voting forums are set for this server.")
            return

        channels = [f"<#{forum_id}>" for forum_id in voting_forums]
        embed = discord.Embed(title="🗳 **Voting Forums**", description="\n".join(channels), color=discord.Color.green())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))