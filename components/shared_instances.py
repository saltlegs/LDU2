# this file should not import any other files in the bot to avoid circular imports
# it is for storing "global" objects that are used across the whole bot

version = "v1.3.6"

DEVTAG = "laukins"

import discord
from discord.ext import commands
from pathlib import Path

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True


bot = commands.Bot(intents=intents, command_prefix='drigoydgjamdiuhfnsgihfjsfthsft')
# idiot prefix that i can't turn off so i made it very long such that nobody will ever trigger it
shcogs = []

tree = bot.tree

### logger ###

logged_amount = 0

### assets ###

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TYPEFACE_DIR = PROJECT_ROOT / 'assets' / 'type'

### points ###

POINTS_DATABASE = {} # not great practice to have this here but whatevs