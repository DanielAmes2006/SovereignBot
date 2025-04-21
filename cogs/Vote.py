import discord
from discord.ext import commands
from discord import app_commands
import json
import os

SERVER_INFO_FILE = os.path.join(os.path.dirname(__file__), "..", "server_info.json")

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
        self.active_votes = {}  # Tracks ongoing votes

    @commands.command()
    async def add_voting_forum(self, ctx, channel: discord.TextChannel):
        """ Adds a voting forum dynamically (Prefix Command) """
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
        server_info[guild_id]["voting_forums"] = voting_forforums
        save_server_info(server_info)

        await ctx.send(f"✅ **{channel.name}** has been added as a voting forum!")

    @app_commands.command(name="add_voting_forum", description="Adds a voting forum dynamically")
    async def slash_add_voting_forum(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """ Calls the existing add_voting_forum command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.add_voting_forum, channel)
        await interaction.response.send_message(f"✅ Added {channel.mention} as a voting forum!", ephemeral=True)

    @commands.command()
    async def remove_voting_forum(self, ctx, channel: discord.TextChannel):
        """ Removes a voting forum dynamically (Prefix Command) """
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

    @app_commands.command(name="remove_voting_forum", description="Removes a voting forum dynamically")
    async def slash_remove_voting_forum(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """ Calls the existing remove_voting_forum command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.remove_voting_forum, channel)
        await interaction.response.send_message(f"✅ Removed {channel.mention} from voting forums!", ephemeral=True)

    @commands.command()
    async def list_voting_forums(self, ctx):
        """ Lists all active voting forums (Prefix Command) """
        guild_id = str(ctx.guild.id)
        voting_forums = get_server_setting(ctx.guild.id, "voting_forums") or []

        if not voting_forums:
            await ctx.send("⚠️ No voting forums are set for this server.")
            return

        channels = [f"<#{forum_id}>" for forum_id in voting_forums]
        embed = discord.Embed(title="🗳 **Voting Forums**", description="\n".join(channels), color=discord.Color.green())
        await ctx.send(embed=embed)

    @app_commands.command(name="list_voting_forums", description="Lists all active voting forums")
    async def slash_list_voting_forums(self, interaction: discord.Interaction):
        """ Calls the existing list_voting_forums command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.list_voting_forums)
        await interaction.response.send_message("✅ Listing voting forums!", ephemeral=True)

    @app_commands.command(name="create_vote", description="Starts a vote in a specified channel")
    async def create_vote(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, required_votes: int, question: str):
        """ Creates a voting session """
        embed = discord.Embed(title="🗳 **Vote Started**", description=f"{question}\n\nReact below to vote!", color=discord.Color.blue())
        message = await channel.send(f"{role.mention}", embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")

        self.active_votes[message.id] = {
            "channel": channel.id,
            "required_votes": required_votes,
            "yes_votes": 0,
            "no_votes": 0,
            "message": message
        }
        await interaction.response.send_message(f"✅ Vote created in {channel.mention}!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Vote(bot))
