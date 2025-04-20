import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    """ Custom help command that organizes bot commands per cog """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx, cog_name: str = None):
        """ Displays commands categorized by cog or details for a specific cog (Prefix Command) """

        if cog_name:  # Show commands for a specific cog
            cog = self.bot.get_cog(cog_name)
            if not cog:
                await ctx.send(f"⚠️ **No cog named '{cog_name}' found!**")
                return

            embed = discord.Embed(title=f"📖 **Help: {cog_name} Cog**", color=discord.Color.blue())
            for command in cog.get_commands():
                embed.add_field(name=f"`{command.name}`", value=command.help or "No description available.", inline=False)

            await ctx.send(embed=embed)
            return

        # Show commands categorized under each cog, excluding HelpCog
        embed = discord.Embed(title="📖 **Bot Commands Overview**", description="Use `.help <cog_name>` for details on a specific category.", color=discord.Color.blue())

        for cog_name, cog in self.bot.cogs.items():
            if cog_name == "HelpCog":  # Skip HelpCog
                continue

            command_list = [f"`{command.name}`" for command in cog.get_commands()]
            if command_list:
                embed.add_field(name=f"📂 **{cog_name}**", value=", ".join(command_list), inline=False)

        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="Displays categorized bot commands or details for a specific cog")
    async def help_slash(self, interaction: discord.Interaction, cog_name: str = None):
        """ Displays commands categorized by cog or details for a specific cog (Slash Command) """

        if cog_name:  # Show commands for a specific cog
            cog = self.bot.get_cog(cog_name)
            if not cog:
                await interaction.response.send_message(f"⚠️ **No cog named '{cog_name}' found!**", ephemeral=True)
                return

            embed = discord.Embed(title=f"📖 **Help: {cog_name} Cog**", color=discord.Color.blue())
            for command in cog.get_commands():
                embed.add_field(name=f"`{command.name}`", value=command.help or "No description available.", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Show commands categorized under each cog, excluding HelpCog
        embed = discord.Embed(title="📖 **Bot Commands Overview**", description="Use `/help <cog_name>` for details on a specific category.", color=discord.Color.blue())

        for cog_name, cog in self.bot.cogs.items():
            if cog_name == "HelpCog":  # Skip HelpCog
                continue

            command_list = [f"`{command.name}`" for command in cog.get_commands()]
            if command_list:
                embed.add_field(name=f"📂 **{cog_name}**", value=", ".join(command_list), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
