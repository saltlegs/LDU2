

import discord
from discord.ext import commands
import os
import sys

from components.shared_instances import bot, tree, version
from components.function.logging import log

log(f"============================================")
log(f"================startup=====================")
log(f"============================================")
log(f"~1C-LDU ~2version {version} ~7starting up...")
log("~1config, ~3levels ~7& ~5discord utility ~7bot")
log("~1(c) 2025-2026 lauren k ~7/ ~4saltlegs.im")

def log_all_commands():
    commands = bot.tree.get_commands()
    log(f"loaded {len(commands)} commands{':' if len(commands) else ''} {', '.join([command.name for command in commands])}")  

async def sync_tree():
    log("syncing tree...")
    await tree.sync()
    log_all_commands()

async def load_all_cogs():
    log("loading cogs...")
    # load all cogs in the components/cogs directory
    for file in os.listdir("components/cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"components.cogs.{file[:-3]}")
            log(f"~2loaded cog {file}")
    log("done loading cogs")


@bot.event
async def on_ready():
    log (f"~1l~2o~3r~4i~5t~6s~1i ~2b~3o~4t~5 ~r(colourtest)")
    log(f"~2successfully logged in as ~1{bot.user}")
    guilds_text = "guilds" if len(bot.guilds) != 1 else "guild"
    guilds_list = ', '.join([f"{guild.name} ({guild.owner.name})" for guild in bot.guilds])
    log(f"~2connected to {len(bot.guilds)} {guilds_text}: ~1{guilds_list}")
    await load_all_cogs()
    activity = discord.Activity(name=f"{version}", type=discord.ActivityType.playing)
    await bot.change_presence(activity=activity)
    
    # goes last always
    await sync_tree()

@bot.event
async def on_guild_join(guild):
    log(f"joined guild {guild.name}")
    await sync_tree()

@bot.event
async def on_guild_remove(guild):
    log(f"removed from guild {guild.name}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        command_name = interaction.data.get("name")
        user = interaction.user
        guild = interaction.guild

        log(f"command /{command_name} used by {user} in {guild.name if guild else 'DMs'}")

try:
    with open("token.txt", "r") as f:
        token = f.read().strip()
except FileNotFoundError:
    with open("token.txt", "w") as f:
        f.write("")
    log("~1please paste your bot token into token.txt in the same directory with main.py.")
    sys.exit()

if not token:
    log("~1please paste your bot token into token.txt in the same directory with main.py.")
    sys.exit()

try:
    bot.run(token)
except discord.errors.LoginFailure:
    log("~1invalid token in token.txt. please check that it is valid.")

