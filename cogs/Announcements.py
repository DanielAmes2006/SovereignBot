import discord
from discord.ext import commands
from discord import app_commands

class AnnouncementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Create an announcement in a specified channel.")
    @app_commands.describe(channel="The channel where the announcement will be sent", message="The announcement message")
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        try:
            # Send the message to the specified channel
            await channel.send(f"📢 **Announcement**: {message}")
            # Notify the user the announcement has been sent
            await interaction.response.send_message(f"Announcement sent to {channel.mention}", ephemeral=True)
        except Exception as e:
            # Handle errors
            await interaction.response.send_message(f"Failed to send announcement: {str(e)}", ephemeral=True)

# Add the cog to your bot
async def setup(bot):
    await bot.add_cog(AnnouncementCog(bot))
