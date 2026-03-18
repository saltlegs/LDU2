import discord
from discord.ext import commands

from components.function.api_shorthand import is_user_banned, does_user_exist, get_member_object

async def note_pre(bot:commands.Bot, interaction:discord.Interaction, target:discord.Member, comment:str):
    return await does_user_exist(target.id, interaction.guild.id)

async def mute_pre(bot:commands.Bot, interaction:discord.Interaction, target:discord.Member, comment:str):
    member = await get_member_object(target.id, interaction.guild.id)
    return await does_user_exist(target.id, interaction.guild.id) and not member.is_timed_out()

async def unmute_pre(bot:commands.Bot, interaction:discord.Interaction, target:discord.Member, comment:str):
    member = await get_member_object(target.id, interaction.guild.id)
    return await does_user_exist(target.id, interaction.guild.id) and member.is_timed_out()

async def ban_pre(bot:commands.Bot, interaction:discord.Interaction, target:discord.Member, comment:str):
    return await does_user_exist(target.id, interaction.guild.id) and not await is_user_banned(target.id, interaction.guild.id)

async def unban_pre(bot:commands.Bot, interaction:discord.Interaction, target:discord.Member, comment:str):
    return await does_user_exist(target.id, interaction.guild.id) and await is_user_banned(target.id, interaction.guild.id)

PREREQUISITES = {
    "note":     note_pre,
    "warn":     note_pre,
    "mute":     mute_pre,
    "unmute":   unmute_pre,
    "ban":      ban_pre,
    "unban":    unban_pre
}