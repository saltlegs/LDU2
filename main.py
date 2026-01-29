

# Suppress discord.py info/debug output
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.gateway").setLevel(logging.ERROR)
logging.getLogger("discord.client").setLevel(logging.ERROR)


import discord
from discord.ext import commands
import os
import sys

from components.shared_instances import bot, tree, version, shcogs
from components.function.logging import log
from components.function.api_shorthand import sync_cogs_for_guild                                                            
log("~5                     ▄▄▄▄            ▄▄                     ")
log("~1                     ▀▀██            ██                     ")
log("~3  ▄█████▄              ██       ▄███▄██  ██    ██           ")
log("~2 ██▀    ▀              ██      ██▀  ▀██  ██    ██           ")
log("~6 ██         █████      ██      ██    ██  ██    ██           ")
log("~4 ▀██▄▄▄▄█              ██▄▄▄   ▀██▄▄███  ██▄▄▄███           ")
log("~5   ▀▀▀▀▀                ▀▀▀▀     ▀▀▀ ▀▀   ▀▀▀▀ ▀▀           ")
log("~1      config, ~3levels ~7& ~5discord utility ~7bot")
log("~7     (c) 2025-2026 lauren k ~7/ ~4saltlegs.im          ")
log(f"~7              (version {version})")

purge_flag_path = "savedata/global_commands_purged.flag"

def int_to_string(i: int) -> str:
    length = (i.bit_length() + 7) // 8
    b = i.to_bytes(length, byteorder="big")
    return b.decode("utf-8")

async def purge_global_commands_once(bot):
    if os.path.exists(purge_flag_path):
        log("global command purge already done, skipping")
        return

    log("purging global commands...")
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    log("global commands cleared!")

    with open(purge_flag_path, "w") as f:
        f.write(f"{int_to_string(9157823193946128403151076878606240331230323)}\n")
    log(f"purge flag written to {purge_flag_path}")

def log_all_commands():
    commands = bot.tree.get_commands()
    log(f"~2loaded {len(commands)} commands:")
    cog_map = {name: [] for name in bot.cogs}
    for cmd in commands:
        qualname = getattr(cmd.callback, "__qualname__", "")
        found = False
        for cog_name, cog in bot.cogs.items():
            if qualname.startswith(cog.__class__.__name__):
                cog_map[cog_name].append(cmd.name)
                found = True
                break
        if not found:
            pass
    for cog, cmds in cog_map.items():
        log(f"~2cog: {cog.lower()}")
        for cmd in cmds:
            log(f"\t- {cmd}")
        if not cmds:
            log(f"\t- (none)")

async def load_all_cogs():
    # load all cogs in the components/cogs directory
    for file in os.listdir("components/cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"components.cogs.{file[:-3]}")


@bot.event
async def on_ready():
    guilds_text = "guilds" if len(bot.guilds) != 1 else "guild"
    log(f"connected to {len(bot.guilds)} {guilds_text}:")
    for guild in bot.guilds:
        log(f"\t- {guild.name} (owner: {guild.owner.name})")
    await load_all_cogs()
    activity = discord.Activity(name=f"{version}", type=discord.ActivityType.playing)
    await bot.change_presence(activity=activity)

    await purge_global_commands_once(bot)
    shcogs[:] = list(bot.cogs.keys())
    for guild in bot.guilds:
        await sync_cogs_for_guild(bot, tree, guild)

@bot.event
async def on_guild_join(guild):
    log(f"joined guild {guild.name}")
    await sync_cogs_for_guild(bot, tree, guild)
    await guild.owner.send(f"thank you for inviting LDU to {guild.name}!\n\nmake sure to have a look at the documentation here: https://www.saltlegs.im/ldu/lduhelp.html\n\nif you need any assistance or have a suggestion, feel free to reach out on our support server: https://discord.gg/hTNWJnmuDK")

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

token = ""
try:
    with open("token.txt", "r") as f:
        token = f.read().strip()
except FileNotFoundError:
    with open("token.txt", "w") as f:
        f.write("")

if not token:
    log("~1please paste your bot token into token.txt in the same directory with main.py.")
    sys.exit()

try:
    bot.run(token)
except discord.errors.LoginFailure:
    log("~1invalid token in token.txt. please check that it is valid.")


