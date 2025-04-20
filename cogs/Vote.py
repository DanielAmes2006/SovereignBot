import discord
from discord.ext import commands
from discord import app_commands

class Vote(commands.Cog):
    """ Handles automated voting systems for forums """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_voting_forum", description="Adds a voting forum dynamically")
    async def slash_add_voting_forum(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """ Calls the existing add_voting_forum command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.add_voting_forum, channel)
        await interaction.response.send_message(f"✅ Added {channel.mention} as a voting forum!", ephemeral=True)

    @app_commands.command(name="remove_voting_forum", description="Removes a voting forum dynamically")
    async def slash_remove_voting_forum(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """ Calls the existing remove_voting_forum command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.remove_voting_forum, channel)
        await interaction.response.send_message(f"✅ Removed {channel.mention} from voting forums!", ephemeral=True)

    @app_commands.command(name="list_voting_forums", description="Lists all active voting forums")
    async def slash_list_voting_forums(self, interaction: discord.Interaction):
        """ Calls the existing list_voting_forums command """
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
