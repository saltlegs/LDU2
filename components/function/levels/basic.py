import discord
import math
import operator
import random

from components.classes.confighandler import ConfigHandler
from components.function.savedata import get_guild_attribute, get_guild_member_attribute
from components.shared_instances import bot, POINTS_DATABASE
from components.function.logging import log

K_FALLBACK = 5.34

def points_to_level(points: int, confighandler: ConfigHandler) -> tuple[int, int]:
    "returns level, remaining points to next level"

    k = confighandler.get_attribute("k", fallback=K_FALLBACK)
    k = K_FALLBACK if k == 0 else k

    points_negative = points < 0
    level = int(math.sqrt(abs(points)) / k)
    level = -level if points_negative else level

    xp_current = (level * k) ** 2       # total xp required to reach current level
    xp_next = ((level + 1) * k) ** 2    #  total xp required to reach next level

    remaining_points = xp_next - points # points needed to reach next level from where we are now

    return level, int(remaining_points)


def level_to_points(level: int, confighandler: ConfigHandler) -> int:
    k = confighandler.get_attribute("k", fallback=K_FALLBACK)

    # total xp required to reach this level
    return int((level * k) ** 2)

def get_guild_leaderboard(guild_id: int) -> list[tuple[int, int]]:
    """returns the guild's leaderboard sorted high to low"""
    points_db = get_guild_attribute(guild_id, "points_data")
    if not isinstance(points_db, dict):
        log("~1tried to get guild leaderboard, failed due to missing or malformed data")
        return [] # no data or malformed data
    log("~2attempting to sort leaderboard data")
    leaderboard = sorted(points_db.items(), key=operator.itemgetter(1), reverse=True)
    log("~2successfully sorted leadboard data")
    return leaderboard

def get_user_position(guild_id: int, target_user_id: int) -> int:
    leaderboard = get_guild_leaderboard(guild_id)

    for position, (user_id, points) in enumerate(leaderboard):
        if user_id == target_user_id:
            return position + 1
    return -1 # if the user is not found in the leaderboard

def get_user_progress(level, total, points_to_next_level, confighandler):

    points_for_current_level = level_to_points(level, confighandler)
    points_since_last_level = total - points_for_current_level

    try:
        progress = points_since_last_level / (points_since_last_level + points_to_next_level)
        progress = min(progress, 1)
        progress = max(progress, 0)
    except ZeroDivisionError:
        progress = 1

    return progress

    # entry format: 
    # 0 DISPLAY NAME,       1 USER NAME, 
    # 2 UUID,               3 LEVEL, 
    # 4 TOTAL POINTS,       5 POINTS TO NEXT LEVEL, 
    # 6 PROGRESS,           7 USER THEME

def format_leaderboard(guild_id: int, confighandler: ConfigHandler) -> list[tuple[str, str, int, int, int, int]]:
    """returns a list of tuples: \n\nDISPLAY NAME, USER NAME, UUID, LEVEL, TOTAL POINTS, POINTS TO NEXT LEVEL"""
    leaderboard = get_guild_leaderboard(guild_id)
    guild = bot.get_guild(guild_id)

    formatted_leaderboard = []
    for user_id, points in leaderboard:
        user = guild.get_member(user_id)

        if not user:
            continue # skip if no such user exists

        displayname = user.display_name
        username = user.name
        total_points = int(points)
        level, points_to_next = points_to_level(points, confighandler)

        progress = get_user_progress(level, total_points, points_to_next, confighandler)
        user_theme = get_guild_member_attribute(guild_id, user_id, "colour")

        entry = (displayname, username, user_id, level, total_points, points_to_next, progress, user_theme)
        formatted_leaderboard.append(entry)

    return formatted_leaderboard

def is_valid_range(given_range):
    if not isinstance(given_range, tuple):
        return False
    if not len(given_range) == 2:
        return False
    both_are_int = ( isinstance(given_range[0], int) and isinstance(given_range[1], int) )
    return both_are_int
        

def increment_user_points(guild:discord.Guild, user:discord.User, amount, confighandler:ConfigHandler) -> tuple[int, bool]:
    """increment a users points with either a set integer amount or a integer range (amount can be int or a valid 2 integer tuple). 
    returns the new point value and a bool: True if the user has levelled up and False otherwise."""

    # type checking

    if isinstance(amount, list):
        amount = tuple(amount)

    if isinstance(amount, tuple):
        if is_valid_range(amount):
            amount = random.randint(*amount)
        else:
            raise TypeError(f"tuple value {amount} passed to increment_user_points is not a valid range")
    elif not isinstance(amount, int):
        raise TypeError(f"value {amount} passed to increment_user_points is not an integer or valid tuple range")
    
    # validate existence of user & guild

    guild_id = guild.id
    guild_name = guild.name
    user_id = user.id
    user_name = user.name

    if guild_id not in POINTS_DATABASE:
        POINTS_DATABASE[guild_id] = {}
    if user_id not in POINTS_DATABASE[guild_id]:
        POINTS_DATABASE[guild_id][user_id] = 0

    # get their current level

    user_points_before = POINTS_DATABASE[guild_id][user_id]
    user_level_before, _  = points_to_level(user_points_before, confighandler)

    # increment the user's point value

    POINTS_DATABASE[guild_id][user_id] += amount

    # get their new level

    user_points_after = POINTS_DATABASE[guild_id][user_id]
    user_level_after, _ = points_to_level(user_points_after, confighandler)

    # check if they have levelled up

    has_levelled_up = user_level_after > user_level_before

    log(f"~2added {amount} points to {user_name} in {guild_name}")

    return user_points_after, has_levelled_up

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

def make_palette(main):
    r, g, b = main

    # darker shade
    dark = tuple(int(c * 0.7) for c in (r, g, b))

    # soft grey blend
    grey = tuple(int((c * 0.3) + (220 * 0.7)) for c in (r, g, b))

    # brightness check for text colour
    brightness = 0.299*r + 0.587*g + 0.114*b
    if brightness > 200:
        # if background is very bright, shift text slightly toward grey so it's readable
        text = (220, 220, 220)
    else:
        # otherwise keep it close to white
        text = (245, 245, 245)

    # circle near-black, tinted by the main colour
    circle = tuple(max(0, int(c * 0.15)) for c in (r, g, b))

    def to_int_tuple(value):
        # ensure value is a tuple of ints
        return tuple(int(x) for x in value)

    return {
        "main": to_int_tuple(main),
        "dark": to_int_tuple(dark),
        "grey": to_int_tuple(grey),
        "text": to_int_tuple(text),
        "circle": to_int_tuple(circle),
    }


