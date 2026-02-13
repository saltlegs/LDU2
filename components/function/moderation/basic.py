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

def get_case_embed(
    bot: commands.Bot,
    channel: discord.channel,
    case_id:int,
    case:dict,
):
    case_type = case["type"]
    case_time = case["time"]
    case_end  = case["end"]
    case_note = case["note"]
    if case_end is not None: case_duration = case_end - case_time
    else: case_duration = None
    case_target = bot.get_user(case["target"])
    case_target_avatar = case_target.avatar
    case_target_avatar = case_target_avatar.url if case_target_avatar is not None else bot.user.avatar.url
    case_author = bot.get_user(case["author"])


    embed = discord.Embed(
        title = f"case {case_id}: {case_type}",
        color = discord.Colour.dark_red,
        timestamp = datetime.datetime.now
    )
    embed.add_field(name="user", value=case_target.mention)
    embed.add_field(name="moderator", value=case_author.mention)
    embed.add_field(name="comment", value=case_note)
    embed.set_image(url=case_target_avatar)

    if case_duration is not None:
        duration = get_duration_string(case_duration)
        embed.add_field(name="duration", value=duration)

    return embed

def get_duration_string(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''}"

    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''}"

def str_to_seconds(string:str):
    def minutes_to_seconds(minutes:int): return minutes * 60
    def hours_to_seconds(hours:int):     return hours * 3600
    def days_to_seconds(days:int):       return days * 86400
    def bad_time_unit_error(): raise ValueError(f"invalid time unit in string {string} should resemble 1d5h, 1h30m, etc. valid time units: s, m, h, d")
    def no_time_components_error(): raise ValueError(f"no valid time components in string {string}. should resemble 1d5h, 1h30m, etc")

    components = []
    component = []

    for char in string:
        if char == " ":
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
        if unit   == "s":   seconds += amount
        elif unit == "m":   seconds += minutes_to_seconds(amount)
        elif unit == "h":   seconds += hours_to_seconds(amount)
        elif unit == "d":   seconds += days_to_seconds(amount)
        else: bad_time_unit_error()
    return seconds

