import discord
from discord.ext import commands

class MovGov(commands.Cog):
    """ Placeholder for MovGov functionalities """

    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(MovGov(bot))
