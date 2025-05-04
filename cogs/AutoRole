import discord
from discord.ext import commands

class AutoRole(commands.Cog):
    """Automatically assigns a role to new members joining a specific server"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Assigns a role to new members if they join the designated server"""
        SERVER_ID = 1359995388538523871
        ROLE_ID = 1360678603506847898

        if member.guild.id == SERVER_ID:  # Check if the user joined the specific server
            role = member.guild.get_role(ROLE_ID)
            if role:
                await member.add_roles(role)
                print(f"Assigned role {role.name} to {member.name}.")  # For debugging/logging purposes

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
