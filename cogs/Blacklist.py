import discord
from discord.ext import commands
import json
import os
import asyncio

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

def save_server_info(data):
    """ Saves updated server configuration to JSON file """
    with open(SERVER_INFO_FILE, "w") as file:
        json.dump(data, file, indent=4)

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_mod_perms(self, ctx):
        """ Checks if the user has ANY of the listed mod roles from JSON """
        mod_roles = get_server_setting(ctx.guild.id, "roles")["mod_perms"]
        return any(discord.utils.get(ctx.author.roles, name=role) for role in mod_roles)

    def is_blacklisted(self, user_id, guild_id):
        """ Checks if the user is blacklisted in this server """
        blacklisted_users = get_server_setting(guild_id, "blacklist")
        return str(user_id) in blacklisted_users if blacklisted_users else False

    @commands.command()
    async def blacklist(self, ctx, member: discord.Member):
        """ Adds a user to the blacklist (Only Mod Perms users) """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        if guild_id not in server_info:
            server_info[guild_id] = {"blacklist": []}

        blacklisted_users = server_info[guild_id].get("blacklist", [])
        if str(member.id) in blacklisted_users:
            await ctx.send(f"⚠️ **{member.display_name}** is already blacklisted!")
            return

        blacklisted_users.append(str(member.id))
        server_info[guild_id]["blacklist"] = blacklisted_users
        save_server_info(server_info)

        await ctx.send(f"🚫 **{member.display_name}** has been added to the bot blacklist!")

    @commands.command()
    async def unblacklist(self, ctx, member: discord.Member):
        """ Removes a user from the blacklist (Only Mod Perms users) """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        blacklisted_users = server_info.get(guild_id, {}).get("blacklist", [])
        if str(member.id) not in blacklisted_users:
            await ctx.send(f"✅ **{member.display_name}** is not blacklisted.")
            return

        blacklisted_users.remove(str(member.id))
        server_info[guild_id]["blacklist"] = blacklisted_users
        save_server_info(server_info)

        await ctx.send(f"✅ **{member.display_name}** has been removed from the bot blacklist.")
    
    @commands.command()
    async def temp_blacklist(self, ctx, member: discord.Member, duration: int):
        """ Temporarily blacklists a user for the specified duration """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        if guild_id not in server_info:
            server_info[guild_id] = {"blacklist": []}

        blacklisted_users = server_info[guild_id].get("blacklist", [])
        if str(member.id) in blacklisted_users:
            await ctx.send(f"⚠️ **{member.display_name}** is already blacklisted!")
            return

        blacklisted_users.append(str(member.id))
        server_info[guild_id]["blacklist"] = blacklisted_users
        save_server_info(server_info)

        await ctx.send(f"⏳ **{member.display_name}** is blacklisted for {duration} minutes!")

        # Run unblacklist logic asynchronously to avoid blocking execution
        async def remove_blacklist():
            await asyncio.sleep(duration * 60)
            blacklisted_users.remove(str(member.id))
            server_info[guild_id]["blacklist"] = blacklisted_users
            save_server_info(server_info)
            await ctx.send(f"✅ **{member.display_name}** has been removed from the bot blacklist!")

        # Schedule background task
        asyncio.create_task(remove_blacklist())
    
    @commands.command()
    async def blacklist_list(self, ctx):
        """ Displays the list of blacklisted users """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        blacklisted_users = get_server_setting(guild_id, "blacklist")

        if not blacklisted_users:
            await ctx.send("✅ No blacklisted users in this server.")
            return

        user_list = "\n".join([f"- <@{user_id}>" for user_id in blacklisted_users])
        embed = discord.Embed(title="🚫 Blacklisted Users", description=user_list, color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command()
    async def temp_blacklist(self, ctx, member: discord.Member, duration: int):
        """ Temporarily blacklists a user for the specified duration (Only Mod Perms users) """
        if not self.has_mod_perms(ctx):
            await ctx.send("⛔ You need the **Mod Perms** role to use this command.")
            return

        guild_id = str(ctx.guild.id)
        server_info = load_server_info()

        if guild_id not in server_info:
            server_info[guild_id] = {"blacklist": []}

        blacklisted_users = server_info[guild_id].get("blacklist", [])
        if str(member.id) in blacklisted_users:
            await ctx.send(f"⚠️ **{member.display_name}** is already blacklisted!")
            return

        blacklisted_users.append(str(member.id))
        server_info[guild_id]["blacklist"] = blacklisted_users
        save_server_info(server_info)

        await ctx.send(f"⏳ **{member.display_name}** is blacklisted for {duration} minutes!")

        await asyncio.sleep(duration * 60)  # Wait for the duration to pass

        # Remove user after the time period ends
        blacklisted_users.remove(str(member.id))
        server_info[guild_id]["blacklist"] = blacklisted_users
        save_server_info(server_info)

        await ctx.send(f"✅ **{member.display_name}** has been removed from the bot blacklist!")

    @commands.Cog.listener()
    async def on_message(self, message):
        """ Blocks blacklisted users from using any bot commands """
        if message.author.bot:
            return  # Ignore bot messages

        guild_id = str(message.guild.id)
        blacklisted_users = get_server_setting(guild_id, "blacklist")

        if blacklisted_users and str(message.author.id) in blacklisted_users:
            await message.channel.send(f"⛔ **{message.author.display_name}, you are blacklisted from using this bot!**")
            return

async def setup(bot):
    await bot.add_cog(Blacklist(bot))