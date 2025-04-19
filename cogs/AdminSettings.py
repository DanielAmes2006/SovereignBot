import discord
from discord.ext import commands

class AdminSettings(commands.Cog):
    """ Admin tools for managing bot settings dynamically """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reload_cog(self, ctx, cog_name: str = None):
        """ Reloads a specific cog or all cogs dynamically """

        if not cog_name:  # Reload all cogs
            failed_cogs = []
            for cog in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(cog)
                except Exception as e:
                    failed_cogs.append(f"{cog}: {e}")

            if failed_cogs:
                await ctx.send(f"⚠️ Failed to reload some cogs:\n```{chr(10).join(failed_cogs)}```")
            else:
                await ctx.send("✅ **All cogs reloaded successfully!**")
            return

        # Reload specific cog
        cog_path = f"cogs.{cog_name}"
        try:
            await self.bot.reload_extension(cog_path)
            await ctx.send(f"✅ **Reloaded {cog_name} successfully!**")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to reload `{cog_name}`:\n```{e}```")

async def setup(bot):
    await bot.add_cog(AdminSettings(bot))