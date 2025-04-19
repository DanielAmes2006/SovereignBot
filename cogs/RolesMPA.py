import discord
from discord.ext import commands

# Define XP requirements for roles
ROLE_XP_THRESHOLDS = {
    "Initiate Party Member": 0,
    "Party Member": 10,
    "Active Party Member": 30,
    "Senior Party Member": 50,
    "Party Supervisor": 75,
    "Lead Supervisor": 100,
    "Lead Staff": 130
}

class RolesMPA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def update_roles(self, ctx, user: discord.Member, previous_xp: int, user_xp: dict):
        """ Assigns roles strictly by progression, removes previous ranks, and ensures XP announcements always happen """
        user_id = str(user.id)
        current_xp = user_xp.get(user_id, 0)

        # XP announcement channel (Optional: Adjust or remove this)
        await ctx.send(f"⚡ {user.display_name} now has {current_xp} XP!")

        # Stop modifying ranks if XP is above 150, but keep XP announcements
        if current_xp > 150:
            return  

        previous_role = None

        # Define promotion & demotion channels
        promotion_channel = self.bot.get_channel(1360304802579349611)  
        demotion_channel = self.bot.get_channel(1360304851548114964)  

        for role_name, required_xp in ROLE_XP_THRESHOLDS.items():
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role:
                # Check if user just crossed this threshold (PROMOTION)
                if previous_xp < required_xp <= current_xp:
                    await user.add_roles(role)

                    if promotion_channel:
                        await promotion_channel.send(f"🎉 **{user.display_name}** has been promoted to **{role_name}**!")

                # Identify previous role (DEMOTION)
                if previous_role:
                    old_role = discord.utils.get(ctx.guild.roles, name=previous_role)
                    if old_role and old_role in user.roles:
                        await user.remove_roles(old_role)

                        if demotion_channel:
                            await demotion_channel.send(f"❌ **{user.display_name}** has been demoted from **{previous_role}**.")

            previous_role = role_name  # Update previous role for the next iteration

async def setup(bot):
    await bot.add_cog(RolesMPA(bot))