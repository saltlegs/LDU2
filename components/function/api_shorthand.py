import discord

from components.shared_instances import bot, shcogs
from components.function.savedata import get_guild_attribute, set_guild_attribute

async def is_user_banned(user_id: int, guild_id: int) -> bool:
    """checks if a user is banned in a guild"""
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise ValueError("guild not found")

    try:
        ban = await guild.fetch_ban(discord.Object(id=user_id))
        return True
    except discord.NotFound:
        return False
    except discord.Forbidden:
        raise ValueError("bot does not have permission to view bans")
    except discord.HTTPException:
        raise ValueError("discord API error")


async def sync_cogs_for_guild(bot, tree, guild):
    guild_obj = discord.Object(id=guild.id)
    tree.clear_commands(guild=guild_obj)

    disabled = get_guild_attribute(guild.id, "disabled_cogs")
    disabled = [] if disabled is None else disabled
    mod_disabled_flag = get_guild_attribute(guild.id, "flag_disable_mod_beta")
    if not mod_disabled_flag:
        disabled.append("ModerationBeta")
        set_guild_attribute(guild.id, "flag_disable_mod_beta")
        set_guild_attribute(guild.id, "disabled_cogs", disabled)
    disabled = [] if disabled is None else disabled

    for cog_name, cog in bot.cogs.items():
        if cog_name in disabled:
            continue
        for cmd in cog.get_app_commands():
            tree.add_command(cmd, guild=guild_obj)

    await tree.sync(guild=guild_obj)