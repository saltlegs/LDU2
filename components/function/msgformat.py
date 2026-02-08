# context needed:
# guild
# member

# formats wanted
# username
# displayname
# guildname | servername
# br

# special formats (require regex i think)
# random:1|2|3

import discord

def format_msg(message, guild: discord.Guild, member: discord.Member):

    mention = member.mention
    username = member.name.replace("_", "\_")
    displayname = member.display_name.replace("_", "\_")
    guildname = guild.name.replace("_", "\_")
    br = "\n"

    new_message = str(message)

    new_message = new_message.replace("{mention}", mention)
    new_message = new_message.replace("{username}", username)
    new_message = new_message.replace("{username_lower}", username.lower())
    new_message = new_message.replace("{displayname}", displayname)
    new_message = new_message.replace("{displayname_lower}", displayname.lower())
    new_message = new_message.replace("{guildname}", guildname)
    new_message = new_message.replace("{guildname_lower}", guildname.lower())
    new_message = new_message.replace("{servername}", guildname)
    new_message = new_message.replace("{servername_lower}", guildname.lower())
    new_message = new_message.replace("{br}", br)

    return new_message