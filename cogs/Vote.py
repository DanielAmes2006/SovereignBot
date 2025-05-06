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
    """Handles anonymous voting via Discord buttons."""

    def __init__(self, vote_id: int, question: str, required_votes: int, max_votes: int, cog):
        super().__init__(timeout=None)  # No timeout to allow long-term votes
        self.vote_id = vote_id
        self.question = question
        self.required_votes = required_votes
        self.max_votes = max_votes
        self.cog = cog  # Reference to the Vote cog for tracking votes
        self.votes = {"Aye": 0, "Nay": 0, "Abstain": 0}
        self.double_vote_roles = set(load_double_vote_roles())  # Ensure roles are stored as a set for easy checking

    async def end_vote(self, timeout=False) -> None:
        """Ends the vote and sends results."""
        result_text = "⏳ **Vote ended due to timeout**" if timeout else "✅ **Vote concluded successfully**"
        color = discord.Color.red() if timeout else discord.Color.green()

        embed = discord.Embed(
        title="🗳 **Vote Ended**",
        description=f"**Topic:** {self.question}\n\n✅ **Final Results:**\n👍 Aye: {self.votes['Aye']}\n👎 Nay: {self.votes['Nay']}\n🟡 Abstain: {self.votes['Abstain']}",
        color=discord.Color.green()
    )

        await self.cog.active_votes[self.vote_id]["message"].edit(embed=embed, view=None)
        del self.cog.active_votes[self.vote_id]

    async def handle_vote(self, interaction: discord.Interaction, vote_type: str) -> None:
        """Handles vote button clicks with potential double votes."""
        multiplier = 2 if any(role.id in self.double_vote_roles for role in interaction.user.roles) else 1
        self.votes[vote_type] += multiplier

        total_votes = sum(self.votes.values())
        if total_votes >= self.max_votes:
            await self.end_vote()
            return

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
    """Starts an anonymous vote with the topic displayed."""
    embed = discord.Embed(
        title="🗳 **Anonymous Vote Started**",
        description=f"**Topic:** {question}\n\nClick a button below to vote anonymously!",
        color=discord.Color.blue()
    )

    view = VoteView(len(self.active_votes) + 1, question, required_votes, max_votes, self)
    message = await channel.send(embed=embed, view=view)

    self.active_votes[message.id] = {
        "question": question,  # Ensuring question is stored correctly
        "required_votes": required_votes,
        "max_votes": max_votes,
        "message": message,
        "view": view,
        "end_time": datetime.datetime.utcnow() + datetime.timedelta(days=3)
    }

        view = VoteView(len(self.active_votes) + 1, required_votes, max_votes, question, self)
        message = await channel.send(embed=embed, view=view)

        self.active_votes[message.id] = {
            "question": question,
            "required_votes": required_votes,
            "max_votes": max_votes,
            "message": message,
            "view": view,  # Store the VoteView instance correctly
            "end_time": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }

    @app_commands.command(name="create_vote", description="Starts an anonymous vote using buttons")
    async def create_vote_slash(self, interaction: discord.Interaction, channel: discord.TextChannel, required_votes: int, max_votes: int, question: str) -> None:
        """Slash command version: Starts an anonymous vote"""
        if await self.check_permissions(interaction):
            await self.start_vote(channel, question, required_votes, max_votes)

    @commands.command(name="create_vote")
    async def create_vote_text(self, ctx: commands.Context, channel: discord.TextChannel, required_votes: int, max_votes: int, question: str) -> None:
        """Text command version: Starts an anonymous vote"""
        await self.start_vote(channel, question, required_votes, max_votes)

    @app_commands.command(name="add_vote_role", description="Adds a role that can start votes")
    async def add_vote_role_slash(self, interaction: discord.Interaction, role: discord.Role) -> None:
        """Adds a role to the allowed voting roles list."""
        allowed_roles = load_vote_roles()
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            save_vote_roles(allowed_roles)
            await interaction.response.send_message(f"✅ `{role.name}` can now start votes.")
        else:
            await interaction.response.send_message(f"⚠️ `{role.name}` is already allowed to start votes.")

    @commands.command(name="add_vote_role")
    @commands.has_permissions(administrator=True)
    async def add_vote_role_text(self, ctx: commands.Context, role: discord.Role) -> None:
        """Text command version of adding a vote role"""
        allowed_roles = load_vote_roles()
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            save_vote_roles(allowed_roles)
            await ctx.send(f"✅ `{role.name}` can now start votes.")
        else:
            await ctx.send(f"⚠️ `{role.name}` is already allowed to start votes.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Vote(bot))
