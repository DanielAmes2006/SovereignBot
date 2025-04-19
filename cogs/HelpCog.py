import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    """ Custom help command that organizes bot commands per cog """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, cog_name: str = None):
        """ Displays commands categorized by cog or details for a specific cog """

        if cog_name:
            # Show commands for a specific cog
            cog = self.bot.get_cog(cog_name)
            if not cog:
                await ctx.send(f"⚠️ **No cog named '{cog_name}' found!**")
                return
            
            embed = discord.Embed(title=f"📖 **Help: {cog_name} Cog**", color=discord.Color.blue())
            for command in cog.get_commands():
                embed.add_field(name=f"`{command.name}`", value=command.help or "No description available.", inline=False)

            await ctx.send(embed=embed)
            return

        # Show commands categorized under each cog
        embed = discord.Embed(title="📖 **Bot Commands Overview**", description="Use `.help <cog_name>` for details on a specific category.", color=discord.Color.blue())
        
        for cog_name, cog in self.bot.cogs.items():
            command_list = [f"`{command.name}`" for command in cog.get_commands()]
            if command_list:
                embed.add_field(name=f"📂 **{cog_name}**", value=", ".join(command_list), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))