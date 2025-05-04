import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
import datetime

VOTE_ROLES_FILE = os.path.expanduser("~/SovereignBot/vote_roles.json")

def load_vote_roles():
    """Loads allowed voting roles from file."""
    if os.path.exists(VOTE_ROLES_FILE):
        with open(VOTE_ROLES_FILE, "r") as file:
            return json.load(file)
    return []

def save_vote_roles(role_ids):
    """Saves allowed voting roles to file."""
    with open(VOTE_ROLES_FILE, "w") as file:
        json.dump(role_ids, file, indent=4)

class Vote(commands.Cog):
    """Handles automated voting systems with enhanced functionality"""

    def __init__(self, bot):
        self.bot = bot
        self.active_votes = {}  # Tracks ongoing votes

    async def check_permissions(self, interaction: discord.Interaction):
        """Checks if user has permission to start a vote."""
        allowed_roles = load_vote_roles()
        if any(role.id in allowed_roles for role in interaction.user.roles):
            return True
        await interaction.response.send_message("⚠️ You don't have permission to create votes.", ephemeral=True)
        return False

    async def count_votes(self, vote_message, max_votes):
        """Count votes and determine the outcome."""
        message = await vote_message.channel.fetch_message(vote_message.id)
        reactions = message.reactions
        voters = set()

        tally = {"Aye": 0, "Nay": 0, "Abstain": 0}

        for reaction in reactions:
            async for user in reaction.users():
                if user.bot or user.id in voters:
                    continue

                voters.add(user.id)

                if reaction.emoji == "👍":
                    tally["Aye"] += 1
                elif reaction.emoji == "👎":
                    tally["Nay"] += 1
                elif reaction.emoji == "🟡":
                    tally["Abstain"] += 1

        if sum(tally.values()) >= max_votes:
            return "max_reached", tally

        return "ongoing", tally

    async def start_vote(self, channel, required_votes, max_votes):
        """Core logic for starting a vote."""
        embed = discord.Embed(
            title="🗳 **Vote Started**",
            description=f"React below:\n👍 Aye\n👎 Nay\n🟡 Abstain",
            color=discord.Color.blue()
        )
        message = await channel.send(embed=embed)
        for emoji in ["👍", "👎", "🟡"]:
            await message.add_reaction(emoji)

        self.active_votes[message.id] = {
            "required_votes": required_votes,
            "max_votes": max_votes,
            "message": message,
            "end_time": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }

        while True:
            status, tally = await self.count_votes(message, max_votes)

            if status != "ongoing" or datetime.datetime.utcnow() >= self.active_votes[message.id]["end_time"]:
                result_embed = discord.Embed(
                    title="🗳 **Vote Ended**",
                    description=f"**Results:**\nAye: {tally['Aye']}\nNay: {tally['Nay']}\nAbstain: {tally['Abstain']}",
                    color=discord.Color.green() if status == "max_reached" else discord.Color.red()
                )
                await channel.send(embed=result_embed)
                del self.active_votes[message.id]
                break

            await asyncio.sleep(10)  # Check votes every 10 seconds

    @app_commands.command(name="create_vote", description="Starts a structured vote")
    async def create_vote_slash(self, interaction: discord.Interaction, channel: discord.TextChannel, required_votes: int, max_votes: int):
        """Slash command version: Starts a vote"""
        if await self.check_permissions(interaction):
            await self.start_vote(channel, required_votes, max_votes)

    @commands.command(name="create_vote")
    async def create_vote_text(self, ctx, channel: discord.TextChannel, required_votes: int, max_votes: int):
        """Text command version: Starts a vote"""
        await self.start_vote(channel, required_votes, max_votes)

    async def end_vote(self, channel, message_id):
        """Core logic for ending a vote manually."""
        if message_id not in self.active_votes:
            await channel.send("⚠️ No active vote found with that ID.")
            return

        vote_data = self.active_votes[message_id]
        message = vote_data["message"]
        tally = await self.count_votes(message, vote_data["max_votes"])[1]

        result_embed = discord.Embed(
            title="🗳 **Vote Ended Manually**",
            description=f"**Results:**\nAye: {tally['Aye']}\nNay: {tally['Nay']}\nAbstain: {tally['Abstain']}",
            color=discord.Color.orange()
        )
        await channel.send(embed=result_embed)

        del self.active_votes[message_id]

    @app_commands.command(name="end_vote", description="Manually ends an active vote")
    async def end_vote_slash(self, interaction: discord.Interaction, message_id: int):
        """Slash command version: Manually ends a vote"""
        await self.end_vote(interaction.channel, message_id)

    @commands.command(name="end_vote")
    async def end_vote_text(self, ctx, message_id: int):
        """Text command version: Manually ends a vote"""
        await self.end_vote(ctx.channel, message_id)

    async def list_active_votes(self, channel):
        """Core logic for listing active votes."""
        if not self.active_votes:
            await channel.send("⚠️ No active votes at the moment.")
            return

        embed = discord.Embed(title="🗳 **Active Votes**", color=discord.Color.blue())
        for vote_id, data in self.active_votes.items():
            embed.add_field(
                name=f"Vote ID: {vote_id}",
                value=f"Required Votes: {data['required_votes']}\nMax Votes: {data['max_votes']}\nEnds: {data['end_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}",
                inline=False
            )

        await channel.send(embed=embed)

    @app_commands.command(name="active_votes", description="Lists all ongoing votes")
    async def active_votes_slash(self, interaction: discord.Interaction):
        """Slash command version: Lists active votes"""
        await self.list_active_votes(interaction.channel)

    @commands.command(name="active_votes")
    async def active_votes_text(self, ctx):
        """Text command version: Lists active votes"""
        await self.list_active_votes(ctx.channel)

    @app_commands.command(name="add_vote_role", description="Adds a role that can start votes")
    async def add_vote_role_slash(self, interaction: discord.Interaction, role: discord.Role):
        """Adds a role to the allowed voting roles list."""
        allowed_roles = load_vote_roles()
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            save_vote_roles(allowed_roles)
            await interaction.response.send_message(f"✅ {role.name} can now create votes.")
        else:
            await interaction.response.send_message(f"⚠️ {role.name} is already allowed.")

async def setup(bot):
    await bot.add_cog(Vote(bot))
