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

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_xp = {}

    def has_xp_perms(self, ctx):
        """ Checks if the user has XP permissions """
        xp_roles = get_server_setting(ctx.guild.id, "roles")["xp_perms"]
        return any(discord.utils.get(ctx.author.roles, name=role) for role in xp_roles)

    def has_mod_perms(self, ctx):
        """ Checks if the user has Moderator permissions """
        mod_roles = get_server_setting(ctx.guild.id, "roles")["mod_perms"]
        return any(discord.utils.get(ctx.author.roles, name=role) for role in mod_roles)

    def save_data(self):
        """ Saves XP data to JSON file """
        with open("xp_data.json", "w") as file:
            json.dump(self.user_xp, file, indent=4)

    @commands.command()
    async def xp_add(self, ctx, amount: int, *users: discord.Member):
        """ Adds XP to users (Requires XP Perms) """
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        log_channel_id = get_server_setting(ctx.guild.id, "channels")["logs"]
        log_channel = self.bot.get_channel(log_channel_id)

        for user in users:
            user_id = str(user.id)
            previous_xp = self.user_xp.get(user_id, 0)
            self.user_xp[user_id] = previous_xp + amount

            await self.update_roles(ctx, user, previous_xp)

            if log_channel:
                await log_channel.send(f"📜 **{ctx.author.display_name}** added **{amount} XP** to **{user.display_name}**.")

        self.save_data()
        await ctx.send(f"✅ Added {amount} XP to eligible users!")

    @commands.command()
    async def xp_view(self, ctx, user: discord.Member = None):
        """ View XP of a user (Defaults to command sender) """
        user = user or ctx.author
        xp = self.user_xp.get(str(user.id), 0)
        await ctx.send(f"{user.display_name} has {xp} XP!")

    @commands.command()
    async def xp_set(self, ctx, user: discord.Member, amount: int, *, reason: str = None):
        """ Set XP for a user """
        if not self.has_xp_perms(ctx):
            await ctx.send("⛔ You need the **XP Perms** role to use this command.")
            return

        log_channel_id = get_server_setting(ctx.guild.id, "channels")["logs"]
        log_channel = self.bot.get_channel(log_channel_id)

        user_id = str(user.id)
        previous_xp = self.user_xp.get(user_id, 0)
        self.user_xp[user_id] = max(0, amount)

        await self.update_roles(ctx, user, previous_xp)

        if log_channel:
            await log_channel.send(f"📜 **{ctx.author.display_name}** set XP for **{user.display_name}** to **{amount}**.")

        self.save_data()
        await ctx.send(f"✅ Set {user.display_name}'s XP to {amount}!")

    @commands.command()
    async def leaderboard(self, ctx):
        """ Displays XP leaderboard with pagination """
        sorted_xp = sorted(self.user_xp.items(), key=lambda x: x[1], reverse=True)
        leaderboard_entries = [f"{await self.bot.fetch_user(int(user_id))} - {xp} XP" for user_id, xp in sorted_xp]

        per_page = 10
        total_pages = (len(leaderboard_entries) + per_page - 1) // per_page
        current_page = 0

        async def update_leaderboard(page):
            start_index = page * per_page
            embed = discord.Embed(title="🏆 **Leaderboard**", description="\n".join(leaderboard_entries[start_index:start_index + per_page]), color=discord.Color.blue())
            embed.set_footer(text=f"Page {page + 1} of {total_pages}")
            return embed

        message = await ctx.send(embed=await update_leaderboard(current_page))

        if total_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and reaction.emoji in ["⬅️", "➡️"]

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if reaction.emoji == "⬅️" and current_page > 0:
                        current_page -= 1
                    elif reaction.emoji == "➡️" and current_page < total_pages - 1:
                        current_page += 1

                    await message.edit(embed=await update_leaderboard(current_page))
                    await message.remove_reaction(reaction.emoji, user)

                except asyncio.TimeoutError:
                    break

    async def update_roles(self, ctx, user, previous_xp):
        """ Assigns roles strictly by progression, removes previous ranks, and ensures XP announcements """
        role_thresholds = get_server_setting(ctx.guild.id, "roles")["xp_roles"]
        promotion_channel = self.bot.get_channel(get_server_setting(ctx.guild.id, "channels")["promotion"])
        demotion_channel = self.bot.get_channel(get_server_setting(ctx.guild.id, "channels")["demotion"])

        user_id = str(user.id)
        current_xp = self.user_xp.get(user_id, 0)

        previous_role = None

        for role_name, required_xp in role_thresholds.items():
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role:
                if previous_xp < required_xp <= current_xp:
                    await user.add_roles(role)
                    if promotion_channel:
                        await promotion_channel.send(f"🎉 **{user.display_name}** has been promoted to **{role_name}**!")

                if previous_role:
                    old_role = discord.utils.get(ctx.guild.roles, name=previous_role)
                    if old_role and old_role in user.roles:
                        await user.remove_roles(old_role)
                        if demotion_channel:
                            await demotion_channel.send(f"❌ **{user.display_name}** has been demoted from **{previous_role}**.")

            previous_role = role_name

async def setup(bot):
    await bot.add_cog(XPSystem(bot))