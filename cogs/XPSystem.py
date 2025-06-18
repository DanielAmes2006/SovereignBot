import discord
from discord.ext import commands
import asyncpg

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_url = "postgresql://username:password@your-aws-rds-endpoint/dbname"
        self.bot.loop.create_task(self.initialize_database())

    async def initialize_database(self):
        """Creates database tables on AWS RDS if they don’t exist"""
        conn = await asyncpg.connect(self.db_url)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS xp_systems (
            guild_id BIGINT,
            system_name TEXT,
            PRIMARY KEY (guild_id, system_name)
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_xp (
            guild_id BIGINT,
            user_id BIGINT,
            system_name TEXT,
            xp INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, system_name)
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS default_xp_system (
            guild_id BIGINT PRIMARY KEY,
            system_name TEXT
        )
        """)
        await conn.close()
        print("AWS PostgreSQL database initialized!")

    @discord.app_commands.command(name="add_xp_system", description="Adds a new XP system for the server")
    async def add_xp_system(self, interaction: discord.Interaction, system_name: str):
        """Adds a new XP system for the server"""
        guild_id = interaction.guild.id
        conn = await asyncpg.connect(self.db_url)

        await conn.execute("INSERT INTO xp_systems (guild_id, system_name) VALUES ($1, $2) ON CONFLICT DO NOTHING", guild_id, system_name)
        await conn.execute("INSERT INTO default_xp_system (guild_id, system_name) VALUES ($1, $2) ON CONFLICT DO NOTHING", guild_id, system_name)

        await conn.close()
        await interaction.response.send_message(f"XP system `{system_name}` added!")

    @discord.app_commands.command(name="set_default_xp", description="Sets the default XP system for the server")
    async def set_default_xp(self, interaction: discord.Interaction, system_name: str):
        """Sets the default XP system for the server"""
        guild_id = interaction.guild.id
        conn = await asyncpg.connect(self.db_url)

        await conn.execute("UPDATE default_xp_system SET system_name = $1 WHERE guild_id = $2", system_name, guild_id)
        await conn.close()

        await interaction.response.send_message(f"Default XP system set to `{system_name}`.")

    @discord.app_commands.command(name="add_xp", description="Adds XP to a specific system for a user")
    async def add_xp(self, interaction: discord.Interaction, member: discord.Member, system_name: str, xp_amount: int):
        """Manually adds XP to a specified XP system"""
        guild_id = interaction.guild.id
        user_id = member.id
        conn = await asyncpg.connect(self.db_url)

        await conn.execute("INSERT INTO user_xp (guild_id, user_id, system_name, xp) VALUES ($1, $2, $3, $4) ON CONFLICT(guild_id, user_id, system_name) DO UPDATE SET xp = user_xp.xp + $4",
                           guild_id, user_id, system_name, xp_amount)

        await conn.close()
        await interaction.response.send_message(f"Added `{xp_amount}` XP to `{system_name}` for {member.mention}.")

    @discord.app_commands.command(name="remove_xp", description="Removes XP from a specific system for a user")
    async def remove_xp(self, interaction: discord.Interaction, member: discord.Member, system_name: str, xp_amount: int):
        """Manually removes XP from a specified XP system"""
        guild_id = interaction.guild.id
        user_id = member.id
        conn = await asyncpg.connect(self.db_url)

        await conn.execute("UPDATE user_xp SET xp = GREATEST(0, xp - $1) WHERE guild_id = $2 AND user_id = $3 AND system_name = $4",
                           xp_amount, guild_id, user_id, system_name)

        await conn.close()
        await interaction.response.send_message(f"Removed `{xp_amount}` XP from `{system_name}` for {member.mention}.")

    @discord.app_commands.command(name="xp", description="Shows XP for a user in a specific system or default")
    async def xp(self, interaction: discord.Interaction, member: discord.Member = None, system_name: str = None):
        """Displays XP for a user in a specific system or default"""
        if member is None:
            member = interaction.user

        guild_id = interaction.guild.id
        user_id = member.id
        conn = await asyncpg.connect(self.db_url)

        if system_name is None:
            result = await conn.fetchrow("SELECT system_name FROM default_xp_system WHERE guild_id = $1", guild_id)
            system_name = result["system_name"] if result else "Default"

        result = await conn.fetchrow("SELECT xp FROM user_xp WHERE guild_id = $1 AND user_id = $2 AND system_name = $3", guild_id, user_id, system_name)
        xp_amount = result["xp"] if result else 0

        await conn.close()
        await interaction.response.send_message(f"{member.mention} has `{xp_amount}` XP in `{system_name}`.")

    @commands.Cog.listener()
    async def on_ready(self):
        """Syncs the slash commands globally when the bot is ready"""
        await self.bot.tree.sync()
        print("Slash commands synced!")

def setup(bot):
    bot.add_cog(XPSystem(bot))
