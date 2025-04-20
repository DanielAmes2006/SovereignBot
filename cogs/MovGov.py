import discord
from discord.ext import commands

# Define the allowed server ID
ALLOWED_SERVER_ID = 1361374907304247346

class MovGov(commands.Cog):
    """ Loads only for the specified server """

    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    """ Loads the cog only if the bot is running in the specified server """
    if any(guild.id == ALLOWED_SERVER_ID for guild in bot.guilds):
        await bot.add_cog(MovGov(bot))
    else:
        print(f"⚠️ Skipping MovGov: Bot is not in the allowed server ({ALLOWED_SERVER_ID})")
