import discord
from discord.ext import commands
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
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Store warnings per server

    def get_warnings_file(self, guild_id):
        return f"warnings_{guild_id}.json"

    def load_warnings(self, guild_id):
        """ Loads warnings from JSON file per server """
        warnings_file = self.get_warnings_file(guild_id)
        if os.path.exists(warnings_file):
            with open(warnings_file, "r") as file:
                return json.load(file)
        return {}

    def save_warnings(self, guild_id, warnings_data):
        """ Saves warnings to the correct JSON file per server """
        warnings_file = self.get_warnings_file(guild_id)
        with open(warnings_file, "w") as file:
            json.dump(warnings_data, file)

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
        warnings = self.load_warnings(guild_id)
        user_id = str(member.id)

        if user_id not in warnings:
            warnings[user_id] = []

        warnings[user_id].append({"reason": reason, "moderator": ctx.author.name})
        self.save_warnings(guild_id, warnings)

        await ctx.send(f"⚠️ {member.mention} has been warned for: {reason}")

    @commands.command()
    async def view_warnings(self, ctx, member: discord.Member):
        """ Show warnings specific to this server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = ctx.guild.id
        warnings = self.load_warnings(guild_id)

        if str(member.id) not in warnings or len(warnings[str(member.id)]) == 0:
            await ctx.send(f"{member.mention} has no warnings.")
            return

        embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.orange())
        for idx, warning in enumerate(warnings[str(member.id)], start=1):
            embed.add_field(name=f"Warning {idx}", value=f"Reason: {warning['reason']} | Moderator: {warning['moderator']}", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def clear_warnings(self, ctx, member: discord.Member):
        """ Clears all warnings for a user in this server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = ctx.guild.id
        warnings = self.load_warnings(guild_id)

        if str(member.id) not in warnings or len(warnings[str(member.id)]) == 0:
            await ctx.send(f"{member.mention} has no warnings to clear.")
            return

        warnings[str(member.id)] = []
        self.save_warnings(guild_id, warnings)

        await ctx.send(f"✅ All warnings for {member.mention} have been cleared.")

    @commands.command()
    async def clear_warning(self, ctx, member: discord.Member, warning_index: int):
        """ Clears a specific warning from the user """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = ctx.guild.id
        warnings = self.load_warnings(guild_id)

        if str(member.id) not in warnings or len(warnings[str(member.id)]) == 0:
            await ctx.send(f"{member.mention} has no warnings to clear.")
            return

        if warning_index < 1 or warning_index > len(warnings[str(member.id)]):
            await ctx.send(f"⚠️ Invalid warning index. {member.mention} only has {len(warnings[str(member.id)])} warnings.")
            return

        removed_warning = warnings[str(member.id)].pop(warning_index - 1)
        self.save_warnings(guild_id, warnings)

        await ctx.send(f"✅ Cleared warning {warning_index} for {member.mention}: Reason: {removed_warning['reason']}")

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """ Kick a user from the server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await member.kick(reason=reason)
        await ctx.send(f"👢 **{member.mention} has been kicked!** Reason: {reason}")

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """ Ban a user from the server """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member.mention} has been banned!** Reason: {reason}")

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

    @commands.command()
    async def clear(self, ctx, amount: int):
        """ Deletes a number of messages """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Cleared {amount} messages!", delete_after=3)

async def setup(bot):
    await bot.add_cog(Moderation(bot))