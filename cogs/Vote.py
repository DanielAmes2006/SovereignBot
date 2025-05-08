import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
import datetime

VOTE_ROLES_FILE = os.path.expanduser("~/SovereignBot/vote_roles.json")
DOUBLE_VOTE_FILE = os.path.expanduser("~/SovereignBot/DoubleVoteRoles.json")

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

def load_double_vote_roles():
    """Loads roles that grant double voting power."""
    if os.path.exists(DOUBLE_VOTE_FILE):
        with open(DOUBLE_VOTE_FILE, "r") as file:
            return json.load(file)
    return []

class VoteView(discord.ui.View):
    """Handles anonymous voting via Discord buttons with a single-vote restriction."""

    def __init__(self, vote_id: int, question: str, required_votes: int, max_votes: int, cog):
        super().__init__(timeout=None)  # No timeout to allow long-term votes
        self.vote_id = vote_id
        self.question = question
        self.required_votes = required_votes
        self.max_votes = max_votes
        self.cog = cog
        self.votes = {"Aye": 0, "Nay": 0, "Abstain": 0}
        self.user_votes = set()  # Track users who have already voted
        self.double_vote_roles = set(load_double_vote_roles())

    async def end_vote(self, timeout=False) -> None:
        """Ends the vote and sends results."""
        if self.vote_id not in self.cog.active_votes:
            print(f"⚠️ Error: Vote ID {self.vote_id} not found in active_votes")
            return  # Prevents KeyError

        vote_data = self.cog.active_votes[self.vote_id]
        message = vote_data["message"]

        result_text = "⏳ **Vote ended due to timeout**" if timeout else "✅ **Vote concluded successfully**"
        color = discord.Color.red() if timeout else discord.Color.green()

        embed = discord.Embed(
            title=f"🗳 **Vote #{self.vote_id} Ended**",
            description=f"**Topic:** {self.question}\n\n✅ **Final Results:**\n👍 Aye: {self.votes['Aye']}\n👎 Nay: {self.votes['Nay']}\n🟡 Abstain: {self.votes['Abstain']}",
            color=color
        )

        await message.edit(embed=embed, view=None)
        del self.cog.active_votes[self.vote_id]  # Remove vote after completion

    async def handle_vote(self, interaction: discord.Interaction, vote_type: str) -> None:
        """Handles vote button clicks with single vote restriction and updates tally dynamically."""
        if interaction.user.id in self.user_votes:
            await interaction.response.send_message("⚠️ You have already voted in this poll.", ephemeral=True)
            return  # Prevents multiple votes

        multiplier = 2 if any(role.id in self.double_vote_roles for role in interaction.user.roles) else 1
        self.votes[vote_type] += multiplier
        self.user_votes.add(interaction.user.id)  # Store user ID to prevent multi-voting

        # Update embed with live vote tally
        embed = discord.Embed(
            title=f"🗳 **Vote #{self.vote_id} Ongoing**",
            description=f"**Topic:** {self.question}\n\nCurrent tally:\n👍 Aye: {self.votes['Aye']}\n👎 Nay: {self.votes['Nay']}\n🟡 Abstain: {self.votes['Abstain']}",
            color=discord.Color.blue()
        )

        await self.cog.active_votes[self.vote_id]["message"].edit(embed=embed)
        await interaction.response.send_message(f"✅ You voted **{vote_type}** anonymously!", ephemeral=True)

    @discord.ui.button(label="Aye 👍", style=discord.ButtonStyle.success)
    async def aye_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.handle_vote(interaction, "Aye")

    @discord.ui.button(label="Nay 👎", style=discord.ButtonStyle.danger)
    async def nay_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.handle_vote(interaction, "Nay")

    @discord.ui.button(label="Abstain 🟡", style=discord.ButtonStyle.secondary)
    async def abstain_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.handle_vote(interaction, "Abstain")

class Vote(commands.Cog):
    """Handles automated anonymous voting systems with button-based functionality."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_votes = {}  # Tracks ongoing votes

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """Checks if user has permission to start a vote."""
        allowed_roles = set(load_vote_roles())
        if any(role.id in allowed_roles for role in interaction.user.roles):
            return True
        await interaction.response.send_message("⚠️ You don't have permission to create votes.", ephemeral=True)
        return False

    async def start_vote(self, channel: discord.TextChannel, required_votes: int, max_votes: int, question: str) -> None:
        """Starts an anonymous vote with live tally updates."""
        vote_id = len(self.active_votes) + 1  # Auto-generates a unique vote ID

        embed = discord.Embed(
            title=f"🗳 **Vote #{vote_id} Started**",
            description=f"**Topic:** {question}\n\nClick a button below to vote anonymously!",
            color=discord.Color.blue()
        )

        view = VoteView(vote_id, question, required_votes, max_votes, self)
        message = await channel.send(embed=embed, view=view)

        self.active_votes[vote_id] = {  # Use vote_id as key instead of message.id
            "question": question,
            "required_votes": required_votes,
            "max_votes": max_votes,
            "message": message,
            "view": view,
            "end_time": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }

    @app_commands.command(name="create_vote", description="Starts an anonymous vote using buttons")
    async def create_vote_slash(self, interaction: discord.Interaction, channel: discord.TextChannel, required_votes: int, max_votes: int, question: str) -> None:
        """Slash command version: Starts an anonymous vote"""
        if await self.check_permissions(interaction):
            await self.start_vote(channel, required_votes, max_votes, question)

    @commands.command(name="create_vote")
    async def create_vote_text(self, ctx: commands.Context, channel: discord.TextChannel, required_votes: int, max_votes: int, *question: str) -> None:
        """Text command version: Starts an anonymous vote"""
        question = " ".join(question)  # Convert tuple to string for full question support
        await self.start_vote(channel, required_votes, max_votes, question)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Vote(bot))
