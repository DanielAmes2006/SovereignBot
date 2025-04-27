import discord
from discord.ext import commands
from discord import app_commands

class AdminSettings(commands.Cog):
    """ Admin tools for managing bot settings dynamically """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload_modules")
    @commands.has_permissions(administrator=True)
    async def reload_modules(self, ctx, cog_name: str = None):
        """ Reloads a specific module or all modules dynamically (Prefix Command) """

        if not cog_name:  # Reload all cogs
            failed_cogs = []
            for cog in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(cog)
                except Exception as e:
                    failed_cogs.append(f"{cog}: {e}")

            if failed_cogs:
                await ctx.send(f"⚠️ Failed to reload some modules:\n```{chr(10).join(failed_cogs)}```")
            else:
                await ctx.send("✅ **All modules reloaded successfully!**")
            return

        # Reload specific module
        cog_path = f"cogs.{cog_name}"
        try:
            await self.bot.reload_extension(cog_path)
            await ctx.send(f"✅ **Reloaded {cog_name} successfully!**")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to reload `{cog_name}`:\n```{e}```")

    @app_commands.command(name="reload_modules", description="Reloads a specific module or all modules dynamically")
    async def reload_modules_slash(self, interaction: discord.Interaction, cog_name: str = None):
        """ Reloads a specific module or all modules dynamically (Slash Command) """
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ You need **Administrator** permissions to reload modules.", ephemeral=True)
            return

        if not cog_name:  # Reload all modules
            failed_cogs = []
            for cog in list(self.bot.extensions):
                try:
                    await interaction.client.reload_extension(cog)
                except Exception as e:
                    failed_cogs.append(f"{cog}: {e}")

            if failed_cogs:
                await interaction.response.send_message(f"⚠️ Failed to reload some modules:\n```{chr(10).join(failed_cogs)}```", ephemeral=True)
            else:
                await interaction.response.send_message("✅ **All modules reloaded successfully!**", ephemeral=True)
            return

        # Reload specific module
        cog_path = f"cogs.{cog_name}"
        try:
            await interaction.client.reload_extension(cog_path)
            await interaction.response.send_message(f"✅ **Reloaded {cog_name} successfully!**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Failed to reload `{cog_name}`:\n```{e}```", ephemeral=True)

    @commands.command()
    async def setup_sovereign_perms(self, ctx):
        """ Creates or ensures the Sovereign Perms role exists """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need **Administrator** permissions to use this command.")
            return
    
        guild = ctx.guild
        sovereign_role = discord.utils.get(guild.roles, name="Sovereign Perms")
    
        if not sovereign_role:
            # Create the Sovereign Perms role
            sovereign_role = await guild.create_role(
                name="Sovereign Perms",
                reason="Sovereign Perms role for encapsulating key permissions"
            )
            await ctx.send("✅ Created the `Sovereign Perms` role!")
        else:
            await ctx.send("ℹ️ The `Sovereign Perms` role already exists!")
    
    @commands.command()
    async def sync_perms(self, ctx):
        """ Adds users with specific roles to Sovereign Perms """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("⛔ You need **Administrator** permissions to use this command.")
            return
    
        guild = ctx.guild
        sovereign_role = discord.utils.get(guild.roles, name="Sovereign Perms")
    
        if not sovereign_role:
            await ctx.send("⛔ Please run `!setup_sovereign_perms` first.")
            return
    
        key_roles = ["XP Perms", "Deployment Perms", "Mod Perms"]
        for role_name in key_roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                for member in role.members:
                    if sovereign_role not in member.roles:
                        await member.add_roles(sovereign_role)
    
        await ctx.send("✅ Synced Sovereign Perms with key roles!")
        
async def setup(bot):
    await bot.add_cog(AdminSettings(bot))
