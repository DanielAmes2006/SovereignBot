import discord
from discord.ext import commands
from discord import app_commands
import json
import os

SERVER_INFO_FILE = "server_info.json"

def load_server_info():
    """ Loads server configuration from JSON file """
    if os.path.exists(SERVER_INFO_FILE):
        with open(SERVER_INFO_FILE, "r") as file:
            return json.load(file)
    return {}

def get_server_setting(guild_id, setting):
    """ Retrieves specific configuration setting for the guild """
    server_info = load_server_info()
    return server_info.get(str(guild_id), {}).get(setting, None)

class Moderation(commands.Cog):
    """ Handles moderation commands for server management """
    
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Store warnings per server

    def has_mod_perms(self, ctx):
        """ Checks if the user has Moderator role dynamically from JSON """
        mod_role_name = get_server_setting(ctx.guild.id, "roles")["mod_perms"]
        return discord.utils.get(ctx.author.roles, name=mod_role_name) is not None

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """ Warn a user and store the warning per server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return
        
        guild_id = ctx.guild.id
        warnings = load_server_info()
        user_id = str(member.id)

        if user_id not in warnings:
            warnings[user_id] = []

        warnings[user_id].append({"reason": reason, "moderator": ctx.author.name})
        with open(SERVER_INFO_FILE, "w") as file:
            json.dump(warnings, file)

        await ctx.send(f"⚠️ {member.mention} has been warned for: {reason}")

    @app_commands.command(name="warn", description="Warn a user in the server")
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """ Calls the warn command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.warn, member=member, reason=reason)
        await interaction.response.send_message(f"⚠️ Warned {member.mention}: {reason}", ephemeral=True)

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """ Kick a user from the server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await member.kick(reason=reason)
        await ctx.send(f"👢 **{member.mention} has been kicked!** Reason: {reason}")

    @app_commands.command(name="kick", description="Kick a user from the server")
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """ Calls the kick command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.kick, member=member, reason=reason)
        await interaction.response.send_message(f"👢 Kicked {member.mention} for: {reason}", ephemeral=True)

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """ Ban a user from the server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member.mention} has been banned!** Reason: {reason}")

    @app_commands.command(name="ban", description="Ban a user from the server")
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """ Calls the ban command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.ban, member=member, reason=reason)
        await interaction.response.send_message(f"🔨 Banned {member.mention} for: {reason}", ephemeral=True)

    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        """ Mutes a user (adds a Muted role) """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await ctx.send("⚠️ **Muted role not found!** Please create a role called 'Muted'.")
            return

        await member.add_roles(muted_role)
        await ctx.send(f"🔇 **{member.mention} has been muted!**")

    @app_commands.command(name="mute", description="Mute a user in the server")
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member):
        """ Calls the mute command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.mute, member=member)
        await interaction.response.send_message(f"🔇 Muted {member.mention}!", ephemeral=True)

    @commands.command()
    async def clear(self, ctx, amount: int):
        """ Deletes a number of messages """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Cleared {amount} messages!", delete_after=3)

    @app_commands.command(name="clear", description="Delete messages in the current channel")
    async def clear_slash(self, interaction: discord.Interaction, amount: int):
        """ Calls the clear command via a slash command """
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.invoke(self.clear, amount=amount)
        await interaction.response.send_message(f"🧹 Cleared {amount} messages!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
