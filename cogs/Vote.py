import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

DOUBLE_VOTE_FILE = os.path.expanduser("~/SovereignBot/DoubleVoteRoles.json")

def load_double_vote_roles():
    """Loads double-vote roles from file."""
    if os.path.exists(DOUBLE_VOTE_FILE):
        with open(DOUBLE_VOTE_FILE, "r") as file:
            return json.load(file)
    return []

def save_double_vote_roles(role_ids):
    """Saves double-vote roles to file."""
    with open(DOUBLE_VOTE_FILE, "w") as file:
        json.dump(role_ids, file, indent=4)

class Vote(commands.Cog):
    """Handles automated voting systems with enhanced functionality"""

    def __init__(self, bot):
        self.bot = bot
        self.active_votes = {}  # Tracks ongoing votes
        self.double_vote_roles = load_double_vote_roles()  # Load roles on cog initialization

    async def count_votes(self, vote_message, required_votes):
        """Count votes and determine the outcome."""
        message = await vote_message.channel.fetch_message(vote_message.id)
        reactions = message.reactions
        voters = set()

        tally = {"Aye": 0, "Nay": 0, "Abstain": 0}

        for reaction in reactions:
            async for user in reaction.users():
                if user.bot:
                    continue

                if user.id in voters:
                    continue  # Prevent double-counting votes across multiple reactions

                voters.add(user.id)
                multiplier = 2 if any(role.id in self.double_vote_roles for role in user.roles) else 1

                if reaction.emoji == "👍":
                    tally["Aye"] += multiplier
                elif reaction.emoji == "👎":
                    tally["Nay"] += multiplier
                elif reaction.emoji == "🟡":
                    tally["Abstain"] += multiplier

        # Check for the threshold
        if tally["Aye"] >= required_votes:
            return "passed", tally
        elif tally["Nay"] >= required_votes:
            return "failed", tally

        return "ongoing", tally

    @app_commands.command(name="create_vote", description="Starts a structured vote")
    async def create_vote(self, interaction: discord.Interaction, channel: discord.TextChannel, question: str, required_votes: int):
        """Starts a vote and monitors its progress"""
        embed = discord.Embed(
            title="🗳 **Vote Started**",
            description=f"{question}\n\nReact below:\n👍 Aye\n👎 Nay\n🟡 Abstain",
            color=discord.Color.blue()
        )
        message = await channel.send(embed=embed)
        for emoji in ["👍", "👎", "🟡"]:
            await message.add_reaction(emoji)

        self.active_votes[message.id] = {"question": question, "required_votes": required_votes, "message": message}

        # Monitor vote progress
        while True:
            status, tally = await self.count_votes(message, required_votes)
            if status != "ongoing":
                result_embed = discord.Embed(
                    title=f"🗳 **Vote {'Passed' if status == 'passed' else 'Failed'}**",
                    description=f"Aye: {tally['Aye']}\nNay: {tally['Nay']}\nAbstain: {tally['Abstain']}",
                    color=discord.Color.green() if status == "passed" else discord.Color.red()
                )
                await channel.send(embed=result_embed)
                del self.active_votes[message.id]
                break

            await asyncio.sleep(10)  # Check the votes every 10 seconds

    @commands.command(name="add_double_vote_role")
    async def add_double_vote_role(self, ctx, role: discord.Role):
        """Adds a role to the double vote list."""
        if role.id not in self.double_vote_roles:
            self.double_vote_roles.append(role.id)
            save_double_vote_roles(self.double_vote_roles)
            await ctx.send(f"✅ {role.name} has been added to the Double Vote roles!")
        else:
            await ctx.send(f"⚠️ {role.name} is already assigned for Double Vote privileges.")

    @commands.command(name="remove_double_vote_role")
    async def remove_double_vote_role(self, ctx, role: discord.Role):
        """Removes a role from the double vote list."""
        if role.id in self.double_vote_roles:
            self.double_vote_roles.remove(role.id)
            save_double_vote_roles(self.double_vote_roles)
            await ctx.send(f"✅ {role.name} has been removed from the Double Vote roles!")
        else:
            await ctx.send(f"⚠️ {role.name} is not assigned for Double Vote privileges.")

    @commands.command(name="list_double_vote_roles")
    async def list_double_vote_roles(self, ctx):
        """Lists all roles with double vote privileges."""
        if not self.double_vote_roles:
            await ctx.send("⚠️ No roles are assigned for Double Vote privileges.")
            return

        role_mentions = [ctx.guild.get_role(role_id).mention for role_id in self.double_vote_roles if ctx.guild.get_role(role_id)]
        embed = discord.Embed(
            title="🗳 **Double Vote Roles**",
            description="\n".join(role_mentions),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))
