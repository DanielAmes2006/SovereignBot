import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv  # Import dotenv for environment variables

# Load .env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

DEFAULT_SERVER_CONFIG = {
    "server_name": "New Server",
    "abbreviation": "NS",
    "channels": {
        "attendance": None,
        "deployment_announcement": None,
        "promotion": None,
        "demotion": None
    },
    "roles": {
        "deployment_perms": "Deployment Perms",
        "mod_perms": ["Mod Perms", "Admin", "Staff"],
        "xp_roles": {
            "Guest": 0
        }
    },
    "blacklist": [],
    "deployment_settings": {
        "max_xp_limit": 150,
        "default_attendance_timeout": 300,
        "default_end_countdown": 1800
    },
    "xp_data": {},
    "protected_roles": []
}

import json
import os

# Initialize bot with command prefix
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Load all cogs dynamically
COGS = ["cogs.Fundamentals", "cogs.Moderator", "cogs.XPSystem", "cogs.Blacklist", "cogs.Vote", "cogs.HelpCog", "cogs.AdminSettings", "cogs.Deployments", "cogs.MovGov", "cogs.Announcements", "cogs.AutoRole"]

async def load_cogs():
    """ Loads all bot cogs dynamically with error handling """
    for cog in COGS:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            print(f"⚠️ Failed to load {cog}: {e}")

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}!")
    await load_cogs()
    await bot.tree.sync()

# Error Handling for Command Failures
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"⚠️ Error: {error}")
    print(f"Error in {ctx.command}: {error}")

def register_server(guild_id):
    """ Auto-registers new servers with default config if missing """
    server_info = load_server_info()

    if str(guild_id) not in server_info:
        # Assign default configuration to the new server
        server_info[str(guild_id)] = DEFAULT_SERVER_CONFIG
        server_info[str(guild_id)]["server_name"] = "Unknown Server"
        
        with open(SERVER_INFO_FILE, "w") as file:
            json.dump(server_info, file, indent=4)

        print(f"✅ New server registered: {guild_id}")

    return server_info[str(guild_id)]

@bot.event
async def on_guild_join(guild):
    """ Registers new servers dynamically when they join """
    register_server(guild.id)
    print(f"🔹 Auto-registered server: {guild.name} ({guild.id})")
    """ Automatically sets up the Sovereign Perms role for new servers """
    sovereign_role = discord.utils.get(guild.roles, name="Sovereign Perms")
    if not sovereign_role:
        await guild.create_role(
            name="Sovereign Perms",
            reason="Automatic creation of Sovereign Perms role"
        )

SERVER_INFO_FILE = "server_info.json"

def load_server_info():
    """ Load server settings from JSON, handling empty or missing files """
    if not os.path.exists(SERVER_INFO_FILE):
        return {}

    with open(SERVER_INFO_FILE, "r") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print("⚠️ JSON file is empty or invalid. Initializing blank config.")
            data = {}

    return data

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: Bot token not found. Please set DISCORD_TOKEN in .env.")
