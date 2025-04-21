import discord
from discord.ext import commands
import asyncio
import time
import json
import os

SERVER_INFO_FILE = os.path.expanduser("~/Sovereignbot/server_info.json")

def load_server_info():
    """ Loads server configuration from JSON file """
    if os.path.exists(SERVER_INFO_FILE):
        with open(SERVER_INFO_FILE, "r") as file:
            return json.load(file)
    return {}

def get_server_setting(guild_id, setting):
    """ Retrieves specific configuration setting for the guild, ensuring a valid dictionary """
    server_info = load_server_info()
    return server_info.get(str(guild_id), {}).get(setting, {})  # Returns {} instead of None

class Deployments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DeploymentActive = False
        self.DeploymentStartTime = None
        self.DeploymentEndTime = None
        self.DeploymentAttendance = []

    def has_deployment_perms(self, ctx):
        """ Check if the user has the Deployment_Perms role dynamically from JSON """
        deployment_role_name = get_server_setting(ctx.guild.id, "roles")["deployment_perms"]
        return discord.utils.get(ctx.author.roles, name=deployment_role_name) is not None

    @commands.command()
    async def deployment_start(self, ctx):
        """ Start a deployment and send an announcement to the deployment channel """
        if not self.has_deployment_perms(ctx):
            await ctx.send("⛔ You need the **Deployment Perms** role to start a deployment.")
            return

        self.DeploymentActive = True
        self.DeploymentStartTime = time.time()

        deployment_channel_id = get_server_setting(ctx.guild.id, "channels")["deployment_announcement"]
        deployment_channel = self.bot.get_channel(deployment_channel_id)
        
        if deployment_channel:
            await deployment_channel.send(
                "# MPA Deployment #\n"
                "**We are now deployed! Join our Voice Chat for easy communication.**\n"
                "- Please run `.deployment_attend` so we can register your XP.\n"
                "@everyone"
            )

        await ctx.send("✅ **Deployment has started!** Related commands are now active.")

    @commands.command()
    async def deployment_end(self, ctx):
        """ End deployment with a countdown (Only Deployment_Perms users) """
        if not self.has_deployment_perms(ctx):
            await ctx.send("⛔ You need the **Deployment_Perms** role to end a deployment.")
            return

        countdown_duration = get_server_setting(ctx.guild.id, "deployment_settings")["default_end_countdown"]
        self.DeploymentEndTime = time.time() + countdown_duration

        await ctx.send(f"⏳ **Deployment will end in {countdown_duration // 60} minutes...**")
        await asyncio.sleep(countdown_duration)

        self.DeploymentActive = False
        self.DeploymentEndTime = None
        await ctx.send("❌ **Deployment has ended!** Commands are now disabled.")

    @commands.command()
    async def deployment_status(self, ctx):
        """ Check deployment status & countdown time for XP registration """
        if self.DeploymentEndTime:
            time_left = int(self.DeploymentEndTime - time.time())
            minutes, seconds = divmod(time_left, 60)
            await ctx.send(f"⏳ **{minutes}m {seconds}s left to register for XP!**")
        else:
            await ctx.send("❌ **No Active Deployment.** No active XP registration period.")

    @commands.command()
    async def deployment_extend(self, ctx, extra_minutes: int):
        """ Extend deployment duration dynamically """
        if not self.has_deployment_perms(ctx):
            await ctx.send("⛔ You need the **Deployment_Perms** role to extend a deployment.")
            return

        if self.DeploymentEndTime:
            self.DeploymentEndTime += extra_minutes * 60
            await ctx.send(f"⏳ **Deployment extended by {extra_minutes} minutes!**")
        else:
            await ctx.send("⚠️ Deployment does not have a countdown. Use `.deployment_end` first.")

    @commands.command()
    async def deployment_cancel(self, ctx):
        """ Immediately cancel deployment """
        if not self.has_deployment_perms(ctx):
            await ctx.send("⛔ You need the **Deployment_Perms** role to cancel a deployment.")
            return

        self.DeploymentActive = False
        self.DeploymentEndTime = None
        await ctx.send("❌ **Deployment has been force-ended!** All related commands are now disabled.")

    @commands.command()
    async def deployment_attend(self, ctx):
        """ Fetch attendance channel dynamically & allow registration """
        guild_id = ctx.guild.id
        attendance_channel_id = get_server_setting(guild_id, "channels")["attendance"]

        if attendance_channel_id:
            attendance_channel = self.bot.get_channel(attendance_channel_id)
            if not attendance_channel:
                await ctx.send("⚠️ Attendance channel not found.")
                return
            
            message = await attendance_channel.send(
                f"📢 **{ctx.author.display_name}** wants to confirm deployment attendance! React with 👍 to approve."
            )

            def check(reaction, user):
                return str(reaction.emoji) == "👍" and self.has_deployment_perms(ctx)

            try:
                await self.bot.wait_for("reaction_add", timeout=300, check=check)
                self.DeploymentAttendance.append(ctx.author.display_name)
                await attendance_channel.send(f"✅ **{ctx.author.display_name} attended the deployment!**")
            except asyncio.TimeoutError:
                await attendance_channel.send(f"⚠️ Attendance request by {ctx.author.display_name} expired.")
        else:
            await ctx.send("⚠️ Attendance channel is not configured for this server.")

    @commands.command()
    async def deployment_log(self, ctx):
        """ Show deployment duration & attendance log """
        if not self.DeploymentStartTime:
            await ctx.send("❌ **No deployment activity to log.**")
            return

        elapsed_time = int(time.time() - self.DeploymentStartTime)
        hours, minutes = divmod(elapsed_time // 60, 60)

        attendees = ", ".join(self.DeploymentAttendance) if self.DeploymentAttendance else "No attendees"

        await ctx.send(f"📜 **Deployment Log**\n🕒 Duration: **{hours}h {minutes}m**\n👥 Attendees: {attendees}")

    #Slash Commands

    @discord.app_commands.command(name="deployment_start", description="Start a deployment and send an announcement - Slash Command")
    async def slash_deployment_start(self, interaction: discord.Interaction):
        """ Start a deployment using a Slash Command """
        await self.deployment_start(interaction)
        await interaction.response.send_message("✅ **Deployment has started!**", ephemeral=True)
        
    @discord.app_commands.command(name="deployment_end", description="End deployment with a countdown - Slash Command")
    async def slash_deployment_end(self, interaction: discord.Interaction):
        """ End deployment with a countdown - Slash Command """
        await self.deployment_end(interaction)
        await interaction.response.send_message("❌ **Deployment has ended!** Commands are now disabled.", ephemeral=True)
        
    @discord.app_commands.command(name="deployment_status", description="Check deployment status & countdown time for XP registration - Slash Command")
    async def slash_deployment_status(self, interaction: discord.Interaction):
        """ Check deployment status using a Slash Command """
        await self.deployment_status(interaction)
        await interaction.response.send_message("📢 **Deployment status checked!**", ephemeral=True)
        
    @discord.app_commands.command(name="deployment_extend", description="Extend deployment duration dynamically - Slash Command")
    async def slash_deployment_extend(self, interaction: discord.Interaction, extra_minutes: int):
        """ Extend deployment duration using a Slash Command """
        await self.deployment_extend(interaction, extra_minutes)
        await interaction.response.send_message(f"⏳ **Deployment extended by {extra_minutes} minutes!**", ephemeral=True)
        
    @discord.app_commands.command(name="deployment_cancel", description="Immediately cancel deployment - Slash Command")
    async def slash_deployment_cancel(self, interaction: discord.Interaction):
        """ Immediately cancel deployment using a Slash Command """
        await self.deployment_cancel(interaction)
        await interaction.response.send_message("❌ **Deployment has been force-ended!** All related commands are now disabled.", ephemeral=True)
    
    @discord.app_commands.command(name="deployment_attend", description="Register deployment attendance - Slash Command")
    async def slash_deployment_attend(self, interaction: discord.Interaction):
        """ Register deployment attendance using a Slash Command """
        await self.deployment_attend(interaction)
        await interaction.response.send_message("📢 **Attendance request sent! React with 👍 to confirm.**", ephemeral=True)
    
    @discord.app_commands.command(name="deployment_log", description="Show deployment duration & attendance log - Slash Command")
    async def slash_deployment_log(self, interaction: discord.Interaction):
        """ Show deployment duration & attendance log using a Slash Command """
        await self.deployment_log(interaction)
        await interaction.response.send_message("📜 **Deployment log requested!**", ephemeral=True)
    
async def setup(bot):
    await bot.add_cog(Deployments(bot))
