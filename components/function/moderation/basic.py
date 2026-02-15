import time
import datetime
import discord
from discord.ext import commands

from components.classes.confighandler import ConfigHandler

def gen_case(
    confighandler:ConfigHandler,
    case_type:str,
    case_target:int,
    case_author:int,
    case_duration_seconds:int=-1,
    case_note:str="no note added",
) -> int:
    cases:dict = confighandler.get_attribute("cases", fallback={})
    last_id:int = confighandler.get_attribute("last_id", fallback=-1)

    case_timestamp = time.time()
    case_end_time = (time.time() + case_duration_seconds) if case_duration_seconds != -1 else None

    new_case = {
        "time": case_timestamp,
        "end": case_end_time,
        "type": case_type,
        "target": case_target,
        "author": case_author,
        "note": case_note
    }
    new_id = last_id + 1

    cases[new_id] = new_case
    confighandler.set_attribute("cases", cases)
    confighandler.set_attribute("last_id", new_id)

    return new_id, new_case

async def try_get_mention(bot: commands.Bot, uid:int):
    user = bot.get_user(uid)
    try:
        if user is None: user = await bot.fetch_user(uid)
    except discord.NotFound:
        return "unknown user"
    return user.mention

async def try_get_avatar_url(bot: commands.Bot, uid:int):
    user = bot.get_user(uid)
    try:
        if user is None: user = await bot.fetch_user(uid)
    except:
        return bot.user.avatar.url
    return user.avatar.url
    

async def get_case_embed(
    bot: commands.Bot,
    channel: discord.channel,
    case_id:int,
    case:dict,
):
    case_time       = case.get("time")
    case_end        = case.get("end")
    case_type       = case.get("type")
    case_target_id  = case.get("target")
    case_author_id  = case.get("author")
    case_note       = case.get("note")

    if case_end is not None: case_duration = case_end - case_time
    else: case_duration = None

    case_target_mention = try_get_mention(bot, case_target_id)
    case_target_avatar = try_get_avatar_url(bot, case_target_id)

    case_author_mention = try_get_mention(bot, case_author_id)
    case_author_avatar = try_get_avatar_url(bot, case_author_id)
    #i forgot i didnt need the avatar but it's abstracted anyway

    embed = discord.Embed(
        title = f"case {case_id}: {case_type}",
        color = discord.Colour.dark_red,
        timestamp = datetime.datetime.now()
    )
    embed.add_field(name="user", value=case_target_mention)
    embed.add_field(name="moderator", value=case_author_mention)
    embed.add_field(name="comment", value=case_note)
    embed.set_image(url=case_target_avatar)

    if case_duration is not None:
        duration = get_duration_string(case_duration)
        embed.add_field(name="duration", value=duration)

    return embed

def get_duration_string(seconds: int) -> str:
    def pluralise(name:str, value:int): return f"{value} {name}{'s' if value != 1 else ''}"
    INTERVALS = (
        ("year",    31536000, 1),   # defined as 365 days exactly
        ("month",   2592000, 3),    # defined as 30 days exactly
        ("week",    604800, 2),
        ("day",     86400, 2),
        ("hour",    3600, 1),
        ("minute",  60, 1),
        ("second",  1, 1)
    )

    duration_string = []
    seconds = abs(seconds)

    for noun, interval_seconds, minimum_to_display in INTERVALS:
        whole_unit = seconds // interval_seconds
        if whole_unit < minimum_to_display: continue

        seconds = seconds % interval_seconds
        if whole_unit != 0: duration_string.append(pluralise(noun, whole_unit))
        if seconds == 0: return ', '.join(duration_string)

    return "0 seconds"

def str_to_seconds(string:str):
    def bad_time_unit_error(): raise ValueError(f"invalid time unit in string {string} should resemble 1d5h, 1h30m, etc. valid time units: s, m, h, d")
    def no_time_components_error(): raise ValueError(f"no valid time components in string {string}. should resemble 1d5h, 1h30m, etc")

    INTERVALS = {
        "y":   31536000,    # defined as 365 days exactly
                            # NO MONTHS conflicts with minutes and also sucks
        "w":   604800,
        "d":   86400,
        "h":   3600,
        "m":   60,
        "s":   1
    }

    components = []
    component = []

    for char in string:
        if char in " ,.;:-_/&+":
            continue
        elif char in "0123456789":
            component.append(char)
        else:
            component.append(char)
            components.append(''.join(component))
            component = []

    if component: bad_time_unit_error()
    if components == []: no_time_components_error()
    
    seconds = 0
    for component in components:
        unit = component[-1]
        if component[:-1] == "": bad_time_unit_error()
        amount = int(component[:-1])

        interval = INTERVALS.get(unit)
        if interval is None: bad_time_unit_error()

        seconds += amount * interval
    return seconds

