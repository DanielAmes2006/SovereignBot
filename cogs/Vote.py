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

def load_double_vote_roles():
    """Loads roles that grant double voting power."""
    if os.path.exists(DOUBLE_VOTE_FILE):
        with open(DOUBLE_VOTE_FILE, "r") as file:
            return json.load(file)
    return []

class VoteView(discord.ui.View):
    """Handles anonymous voting via Discord buttons."""

    def __init__(self, vote_id, question, required_votes, max_votes, cog):
        super().__init__(timeout=None)  # No timeout to allow long-term votes
        self.vote_id = vote_id
        self.question = question
        self.required_votes = required_votes
        self.max_votes = max_votes
        self.cog = cog  # Reference to the Vote cog for tracking votes
        self.votes = {"Aye": 0, "Nay": 0, "Abstain": 0}
        self.double_vote_roles = load_double_vote_roles()

    async def end_vote(self, timeout=False):
        """Ends the vote and sends results."""
        result_text = "⏳ **Vote ended due to timeout**" if timeout else "✅ **Vote concluded successfully**"
        color = discord.Color.red() if timeout else discord.Color.green()

        embed = discord.Embed(
            title="🗳 **Vote Ended**",
            description=f"**Topic:** {self.question}\n\n{result_text}\n\n**Results:**\n👍 Aye: {self.votes['Aye']}\n👎 Nay: {self.votes['Nay']}\n🟡 Abstain: {self.votes['Abstain']}",
            color=color
        )

        await self.cog.active_votes[self.vote_id]["message"].edit(embed=embed, view=None)
        del self.cog.active_votes[self.vote_id]

    async def handle_vote(self, interaction: discord.Interaction, vote_type: str):
        """Handles vote button clicks with potential double votes."""
        multiplier = 2 if any(role.id in self.double_vote_roles for role in interaction.user.roles) else 1
        self.votes[vote_type] += multiplier

        total_votes = sum(self.votes.values())
        if total_votes >= self.max_votes:
            await self.end_vote()
            return

        await interaction.response.send_message(f"✅ You voted **{vote_type}** anonymously!", ephemeral=True)

    @discord.ui.button(label="Aye 👍", style=discord.ButtonStyle.success)
    async def aye_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "Aye")

    @discord.ui.button(label="Nay 👎", style=discord.ButtonStyle.danger)
    async def nay_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "Nay")

    @discord.ui.button(label="Abstain 🟡", style=discord.ButtonStyle.secondary)
    async def abstain_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_vote(interaction, "Abstain")

class Vote(commands.Cog):
    """Handles automated anonymous voting systems with button-based functionality."""

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

    async def start_vote(self, channel, question, required_votes, max_votes):
        """Core logic for starting an anonymous vote."""
        embed = discord.Embed(
            title="🗳 **Anonymous Vote Started**",
            description=f"**Topic:** {question}\n\nClick a button below to vote anonymously!",
            color=discord.Color.blue()
        )

        message = await channel.send(embed=embed, view=VoteView(message.id, question, required_votes, max_votes, self))

        self.active_votes[message.id] = {
            "question": question,
            "required_votes": required_votes,
            "max_votes": max_votes,
            "message": message,
            "end_time": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }

    @app_commands.command(name="create_vote", description="Starts an anonymous vote using buttons")
    async def create_vote_slash(self, interaction: discord.Interaction, channel: discord.TextChannel, question: str, required_votes: int, max_votes: int):
        """Slash command version: Starts an anonymous vote"""
        if await self.check_permissions(interaction):
            await self.start_vote(channel, question, required_votes, max_votes)

    @commands.command(name="create_vote")
    async def create_vote_text(self, ctx, channel: discord.TextChannel, question: str, required_votes: int, max_votes: int):
        """Text command version: Starts an anonymous vote"""
        await self.start_vote(channel, question, required_votes, max_votes)

    async def end_vote(self, channel, message_id):
        """Ends a vote manually."""
        if message_id not in self.active_votes:
            await channel.send("⚠️ No active vote found with that ID.")
            return

        vote_data = self.active_votes[message_id]
        view = vote_data["message"].view
        await view.end_vote()

    @app_commands.command(name="end_vote", description="Manually ends an active vote")
    async def end_vote_slash(self, interaction: discord.Interaction, message_id: int):
        """Slash command version: Manually ends an anonymous vote"""
        await self.end_vote(interaction.channel, message_id)

    @commands.command(name="end_vote")
    async def end_vote_text(self, ctx, message_id: int):
        """Text command version: Manually ends an anonymous vote"""
        await self.end_vote(ctx.channel, message_id)

    async def list_active_votes(self, channel):
        """Lists all ongoing votes."""
        if not self.active_votes:
            await channel.send("⚠️ No active votes at the moment.")
            return

        embed = discord.Embed(title="🗳 **Active Votes**", color=discord.Color.blue())
        for vote_id, data in self.active_votes.items():
            embed.add_field(
                name=f"Vote ID: {vote_id}",
                value=f"**Topic:** {data['question']}\nRequired Votes: {data['required_votes']}\nMax Votes: {data['max_votes']}\nEnds: {data['end_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}",
                inline=False
            )

        await channel.send(embed=embed)

    @app_commands.command(name="active_votes", description="Lists all ongoing anonymous votes")
    async def active_votes_slash(self, interaction: discord.Interaction):
        """Slash command version: Lists active anonymous votes"""
        await self.list_active_votes(interaction.channel)

    @commands.command(name="active_votes")
    async def active_votes_text(self, ctx):
        """Text command version: Lists active anonymous votes"""
        await self.list_active_votes(ctx.channel)

@app_commands.command(name="add_vote_role", description="Adds a role that can start votes")
async def add_vote_role_slash(self, interaction: discord.Interaction, role: discord.Role):
    """Adds a role to the allowed voting roles list."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ You need **Administrator** permissions to modify voting roles.", ephemeral=True)
        return

    allowed_roles = load_vote_roles()
    if role.id not in allowed_roles:
        allowed_roles.append(role.id)
        save_vote_roles(allowed_roles)
        await interaction.response.send_message(f"✅ `{role.name}` can now start votes.")
    else:
        await interaction.response.send_message(f"⚠️ `{role.name}` is already allowed to start votes.")

@commands.command(name="add_vote_role")
@commands.has_permissions(administrator=True)
async def add_vote_role_text(self, ctx, role: discord.Role):
    """Text command version of adding a vote role"""
    allowed_roles = load_vote_roles()
    if role.id not in allowed_roles:
        allowed_roles.append(role.id)
        save_vote_roles(allowed_roles)
        await ctx.send(f"✅ `{role.name}` can now start votes.")
    else:
        await ctx.send(f"⚠️ `{role.name}` is already allowed to start votes.")

async def setup(bot):
    await bot.add_cog(Vote(bot))
