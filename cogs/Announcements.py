import discord
from discord.ext import commands
from discord import app_commands

class AnnouncementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # List of allowed user IDs (replace with actual IDs)
        self.allowed_users = {419903852246990849, 805991845481939014, 832223616640483378}

    @app_commands.command(
        name="announce",
        description="Create an announcement in a specified channel."
    )
    @app_commands.describe(
        channel="The channel where the announcement will be sent",
        message="The announcement message"
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str
    ):
        # Check if the user is in the allowed list
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message(
                "⛔ You do not have permission to use this command.",
                ephemeral=True
            )
            return

        try:
            await channel.send(f"📢 **Announcement**: {message}")
            await interaction.response.send_message(
                f"✅ Announcement sent to {channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Failed to send announcement: {str(e)}",
                ephemeral=True
            )

# Add the cog to your bot
async def setup(bot):
    await bot.add_cog(AnnouncementCog(bot))
