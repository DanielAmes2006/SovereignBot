import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class Vote(commands.Cog):
    """ Handles automated voting systems with enhanced functionality """

    def __init__(self, bot):
        self.bot = bot
        self.active_votes = {}  # Tracks ongoing votes

    async def count_votes(self, vote_message, required_votes, double_vote_role):
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
                multiplier = 2 if double_vote_role in [role.id for role in user.roles] else 1

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
        """ Starts a vote and monitors its progress """
        double_vote_role = discord.utils.get(interaction.guild.roles, name="Double Vote")  # Example role name

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
            status, tally = await self.count_votes(message, required_votes, double_vote_role)
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

    @commands.command(name="add_double_vote")
    async def add_double_vote(self, ctx, user: discord.Member):
        """Assigns the Double Vote role to a user."""
        role = discord.utils.get(ctx.guild.roles, name="Double Vote")
        if not role:
            role = await ctx.guild.create_role(name="Double Vote", color=discord.Color.gold())

        await user.add_roles(role)
        await ctx.send(f"✅ {user.mention} now has the Double Vote role!")

async def setup(bot):
    await bot.add_cog(Vote(bot))
