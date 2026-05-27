import discord
from discord.ext import commands

LDU_GUILD_ID = 1321823613028008037
LDU_CHANNEL_ID = 1493878243260891216

async def send_dev_notif(bot: commands.Bot, content:str):
    ldu_guild = bot.get_guild(LDU_GUILD_ID)
    ldu_channel = ldu_guild.get_channel(LDU_CHANNEL_ID)
    await ldu_channel.send(content)