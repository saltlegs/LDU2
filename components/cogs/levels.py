import discord
from discord.ext import commands
import asyncio
import random
import time
import re
from datetime import datetime, timezone

from components.function.logging import log
from components.function.savedata import set_guild_attribute, get_guild_attribute, get_guild_member_attribute, set_guild_member_attribute
from components.classes.confighandler import ConfigHandler, register_config
from components.shared_instances import POINTS_DATABASE, DEVTAG, shcogs
import components.function.levels.basic as lvbsc
import components.function.levels.image_generation as lvimg

recent_speakers = {}

async def save_points_regular(interval=5):
    while True:
        await asyncio.sleep(interval)
        for guild_id, data in POINTS_DATABASE.items():
            if data:
                set_guild_attribute(guild_id, "points_data", data)



class Levels(commands.Cog):


    def __init__(self, bot: commands.Bot):
        global POINTS_DATABASE
        self.bot = bot
        self.generate_handlers()
        register_config("levels_config")

        self.load_points_data()
        self.autosave_task = None  # track the autosave task
        self.startup_task = self.bot.loop.create_task(self._background_startup())

    async def _background_startup(self):
        await self.bot.wait_until_ready()
        if not self.autosave_task or self.autosave_task.done():
            self.autosave_task = self.bot.loop.create_task(save_points_regular())

    def generate_handlers(self):
        self.confighandlers = {}
        guilds = self.bot.guilds
        for guild in guilds:
            confighandler = ConfigHandler("levels_config", guild)
            self.confighandlers[guild.id] = confighandler

    def load_points_data(self):
        global POINTS_DATABASE
        guilds = self.bot.guilds
        for guild in guilds:
            data = get_guild_attribute(guild.id, "points_data")
            if data is None:
                data = {}
            POINTS_DATABASE[guild.id] = data


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log(f"~2joined guild {guild.name}, regenerating handlers...")
        self.generate_handlers()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        log(f"~2removed from guild {guild.name}, regenerating handlers...")
        self.generate_handlers()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # validation
        if message.author.bot or message.guild is None:
            return
        
        disabled_cogs = get_guild_attribute(message.guild.id, "disabled_cogs")
        if not disabled_cogs:
            disabled_cogs = []
        if "Levels" in disabled_cogs:
            return
        
        confighandler = self.confighandlers.get(message.guild.id, None)
        if confighandler is None:
            log(f"~1could not find config handler for guild {message.guild.name}")
            return

        disabled_channels = confighandler.get_attribute("disabled_channels", fallback=[])
        if message.channel.id in disabled_channels:
            log(f"~1ignoring message by {message.author.name} in disabled channel {message.channel.name} of guild {message.guild.name}")
            return

        # get the points range from the guild's config

        points_range = confighandler.get_attribute("points_range", fallback=(1, 5))
        points_range = tuple(points_range)

        # calculate the amount of xp to granted without bonuses

        lo, hi = points_range
        amount_to_increase = random.randint(lo, hi)

        # calculate long message bonus

        LONG_MESSAGE_LENGTH = 120

        if len(message.content) > LONG_MESSAGE_LENGTH:
            bonus = 0
            for i in range((len(message.content) // LONG_MESSAGE_LENGTH) - 1):
                bonus += random.randint(lo, hi)
                
            # log(f"~2long message bonus: {bonus}")
            amount_to_increase += bonus

        # calculate attachment bonus

        ATTACHMENT_BONUS_MULTIPLIER = 1.5

        if message.attachments:
            bonus = round(random.randint(lo, hi) * ATTACHMENT_BONUS_MULTIPLIER)

            amount_to_increase += bonus
            # log(f"~2attachment bonus: {bonus}")

        # check if the user has sent a message within the cooldown

        timestamp = time.time()
        cooldown = confighandler.get_attribute("message_cooldown", fallback=30)

        last_entry = recent_speakers.get(message.author.id)
        last_spoke, last_points = last_entry if last_entry else (None, None)
        
        if last_spoke and timestamp - last_spoke < cooldown:
            if last_points < amount_to_increase: # if the message is bigger than last then grant the difference in points
                amount_to_increase -= last_points
                amount_to_increase = max(amount_to_increase, 0) # dont deduct
                
                recent_speakers[message.author.id] = (last_spoke, last_points + amount_to_increase)
                
            else: # if the message isn't bigger then just ignore it
                return
        else:
            recent_speakers[message.author.id] = (timestamp, amount_to_increase)

        # increment the points and check if a new role needs to be given

        new_points, has_levelled_up = lvbsc.increment_user_points(guild=message.guild, user=message.author, amount=amount_to_increase, confighandler=confighandler)
        new_level, _ = lvbsc.points_to_level(new_points, confighandler)

        if has_levelled_up:
            await self.level_up(new_level, message.author, message.guild, confighandler)


    async def level_up(self, level, user: discord.User, guild: discord.Guild, confighandler: ConfigHandler):

        guild_name = guild.name


        potential_rewards = confighandler.get_attribute("levels", fallback=None)
        roles_to_give = []
        
        if potential_rewards is not None:
            for check_level in range(1, level + 1):
                if check_level in potential_rewards:
                    role_id = potential_rewards[check_level]
                    role = guild.get_role(role_id)
                    if role and role not in user.roles:
                        roles_to_give.append((check_level, role))
        
        role_up = len(roles_to_give) > 0

        # get strings for each situation

        config_keys = confighandler.get_attribute("keys")

        levelup_message_dm = config_keys["levelup_message_dm"]
        levelup_message = config_keys["levelup_message"]
        roleup_message_dm = config_keys["roleup_message_dm"]
        roleup_message = config_keys["roleup_message"]

        # decide which string to use

        alert_channel = confighandler.get_attribute("alert_channel")

        dm = ( alert_channel is None ) # passed through a variable so we can check later
        if dm:
            alert_message = roleup_message_dm if role_up else levelup_message_dm
        else:
            alert_message = roleup_message if role_up else levelup_message
            alert_message = f"{user.mention} {alert_message}"

        alert_message = f"{alert_message}\n-# you can toggle these messages by doing /shut_up in {guild}"

        # try our best to give the role if applicable

        if role_up:
            for check_level, role in roles_to_give:
                try:
                    await user.add_roles(role)
                    log(f"~2added role {role.name} to {user.name} in {guild_name}")
                except discord.Forbidden:
                    log(f"~1could not add role {role.name} to {user.name} in {guild_name}, bot does not have permission")
                    await guild.owner.send(
                        f"hello! i tried to give a user their level-up role in {guild.name}, "
                        f"but i couldn’t. please check that i have the 'manage roles' permission "
                        f"and that my highest role is above the level-up role in the role list. "
                        f"if the issue persists, please PM @{DEVTAG}."
                    ) 
                except Exception as e:
                    log(f"~1error adding role {role.name} to {user.name} in {guild_name}: {e}")

        # check if the user has toggled off level up pings or if the server setting is off

        shutup = get_guild_member_attribute(guild.id, user.id, "shutup")
        servershutup = confighandler.get_attribute("servershutup", fallback=False)

        shutup = ( shutup or servershutup )

        # format the strings and try our best to send them to the user

        if not shutup:
            alert_message = alert_message.replace("{user}", user.mention)
            alert_message = alert_message.replace("{level}", str(level))
            alert_message = alert_message.replace("{guild}", guild_name)
            if role_up:
                highest_role = max(roles_to_give, key=lambda x: x[0])[1]
                alert_message = alert_message.replace("{role}", highest_role.name)

            if dm:
                try:
                    await user.send(alert_message)
                    log(f"~2sent level up message to {user.name} in DM")
                except discord.Forbidden:
                    log(f"~1could not send level up message to {user.name} in DM, user has DMs disabled")
                    return
            else:
                channel = guild.get_channel(alert_channel)
                await channel.send(alert_message)
                log(f"~2sent level up message to {user.name} in {channel.name}")

    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="add_points", description="add points to a user")
    async def add_points(self, interaction: discord.Interaction, user: discord.User, amount: int):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1add_points: could not find config handler for guild {interaction.guild.name}")
            return

        new_points, has_levelled_up = lvbsc.increment_user_points(guild=interaction.guild, user=user, amount=amount, confighandler=confighandler)
        new_level, _ = lvbsc.points_to_level(new_points, confighandler)

        if has_levelled_up:
            await self.level_up(new_level, user, interaction.guild, confighandler)

        await interaction.response.send_message(f"added {amount} points to {user.mention}", allowed_mentions=discord.AllowedMentions.none())

    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="set_points", description="set points for a user")
    async def set_points(self, interaction: discord.Interaction, user: discord.User, amount: int):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1set_points: could not find config handler for guild {interaction.guild.name}")
            return
        guild_id = interaction.guild.id
        user_id = user.id

        # make sure guild entry actually exists
        if guild_id not in POINTS_DATABASE:
            POINTS_DATABASE[guild_id] = {}

        user_points_before = POINTS_DATABASE[guild_id].get(user_id, 0)
        user_level_before, _ = lvbsc.points_to_level(user_points_before, confighandler)

        # set the new absolute points
        POINTS_DATABASE[guild_id][user_id] = int(amount)
        new_points = POINTS_DATABASE[guild_id][user_id]

        user_level_after, _ = lvbsc.points_to_level(new_points, confighandler)
        has_levelled_up = user_level_after > user_level_before

        if has_levelled_up:
            await self.level_up(user_level_after, user, interaction.guild, confighandler)

        await interaction.response.send_message(f"set {user.mention}'s points to {amount}", allowed_mentions=discord.AllowedMentions.none())


    @discord.app_commands.command(name="shut_up", description="toggle levelup/roleup pings/dms")
    async def shut_up(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(f"this command only works in the server you leveled up in")
            return
        user_id = interaction.user.id

        current_toggle = get_guild_member_attribute(guild_id, user_id, "shutup")
        current_toggle = False if current_toggle == None else current_toggle

        set_guild_member_attribute(guild_id, user_id, key="shutup", value=(not current_toggle))

        if not current_toggle: # was false, now true
            await interaction.response.send_message(f"i won't send you levelup messages anymore")
        else: # was true, now false
            await interaction.response.send_message(f"i will send you levelup messages!")

    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="server_shut_up", description="toggle levelup/roleup pings/dms for the entire server")
    async def server_shut_up(self, interaction: discord.Interaction):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1server_shut_up: could not find config handler for guild {interaction.guild.name}")
            await interaction.response.send_message("there was an error with this guild's confighandler", ephemeral=True)
            return

        current_toggle = confighandler.get_attribute("servershutup", fallback=False)

        confighandler.set_attribute("servershutup", not current_toggle)

        if not current_toggle: # was false, now true
            await interaction.response.send_message(f"i won't send levelup messages in this server anymore")
        else: # was true, now false
            await interaction.response.send_message(f"i will send levelup messages in this server!")
        

    @discord.app_commands.default_permissions(manage_channels=True)
    @discord.app_commands.command(name="set_levelup_channel", description="set the channel that levelup messages are sent in")
    async def set_levelup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1set_levelup_channel: could not find config handler for guild {interaction.guild.name}")
            return
        
        channel_id = channel.id
        
        current_channel = confighandler.get_attribute("alert_channel")
        if channel_id == current_channel:
            confighandler.set_attribute("alert_channel", None)
            await interaction.response.send_message(f"set the current alert channel to DM")
        else:
            confighandler.set_attribute("alert_channel", channel_id)
            verified = confighandler.get_attribute("alert_channel")

            if channel_id == verified:
                await interaction.response.send_message(f"set the current alert channel to <#{channel_id}>")
            else:
                await interaction.response.send_message(f"something went wrong :(")

    @discord.app_commands.default_permissions(manage_channels=True)
    @discord.app_commands.command(name="set_server_theme", description="set the base theme that the leaderboard uses")
    @discord.app_commands.describe(colour="valid hex code ('reset' to reset)")
    async def set_leaderboard_theme(self, interaction: discord.Interaction, colour: str):

        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id is None:
            await interaction.response.send_message("this command can only be used in a server.", ephemeral=True)
            return

        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1set_leaderboard_theme: could not find config handler for guild {interaction.guild.name}")
            return
        


        if not colour.startswith("#") and not colour.lower() == "reset":
            colour = f"#{colour}"
        is_valid_hex = bool(re.fullmatch(r"#([0-9a-fA-F]{6})", colour))
        is_reset = colour.lower() == "reset"

        if not is_valid_hex and not is_reset:
            log(f"~3server {interaction.guild.name} tried to change theme to {colour} (invalid)")
            await interaction.response.send_message(f"not a valid input! need a valid hex colour code or 'reset' to go back to random choice.", ephemeral=True)
            return

        if is_reset:
            confighandler.set_attribute("colour", None)
            log(f"~2server {interaction.guild.name} theme cleared")
            await interaction.response.send_message("the server theme will now be picked randomly")
            return
        else:
            rgb = lvbsc.hex_to_rgb(colour)
            confighandler.set_attribute("colour", rgb)
            log(f"~2server {interaction.guild.name} theme set to {colour} f{rgb}")
            await interaction.response.send_message(f"the server theme base colour has been set to {colour}")
            return
        
    @discord.app_commands.command(name="set_user_theme", description="set your personal theme color for generated images")
    @discord.app_commands.describe(colour="valid hex code ('reset' to reset)")
    async def set_user_theme(self, interaction: discord.Interaction, colour: str):
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id is None:
            await interaction.response.send_message("this command can only be used in a server.", ephemeral=True)
            return

        if not colour.startswith("#"):
            colour = f"#{colour}"
        is_valid_hex = bool(re.fullmatch(r"#([0-9a-fA-F]{6})", colour))
        is_reset = colour.lower() == "reset"

        if not is_valid_hex and not is_reset:
            log(f"~3user {interaction.user.name} tried to change theme to {colour} (invalid)")
            await interaction.response.send_message(f"not a valid input! Need a valid hex colour code or 'reset' to go back to server/default theme.", ephemeral=True)
            return

        if is_reset:
            set_guild_member_attribute(guild_id, user_id, key="colour", value=None)
            log(f"~2user {interaction.user.name} theme cleared")
            await interaction.response.send_message("your personal theme has been reset to the server/default theme.", ephemeral=True)
            return
        else:
            rgb = lvbsc.hex_to_rgb(colour)
            set_guild_member_attribute(guild_id, user_id, key="colour", value=rgb)
            log(f"~2user {interaction.user.name} theme set to {colour} f{rgb}")
            await interaction.response.send_message(f"your personal theme color has been set to {colour}", ephemeral=True)
            return

    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="set_xp_range", description="set a range for xp granted on message")
    async def set_xp_range(self, interaction: discord.Interaction, min:int, max:int):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1set_xp_range: could not find config handler for guild {interaction.guild.name}")
            return
        
        if min < 0 or max < 0 or min > max:
            await interaction.response.send_message("invalid range, make sure 0 <= min <= max", ephemeral=True)
            return
        
        confighandler.set_attribute("points_range", (min, max))
        average = (min + max) // 2
        await interaction.response.send_message(f"set xp range to {min}-{max} (average {average})", ephemeral=True)
        log(f"~2set xp range to {min}-{max} in guild {interaction.guild.name}")

        


    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="set_level_role", description="set a role to be given on level up")
    async def set_level_role(self, interaction: discord.Interaction, level: int, role: discord.Role):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1set_level_role: could not find config handler for guild {interaction.guild.name}")
            return
        
        if level <= 1:
            await interaction.response.send_message("level must be greater than 1", ephemeral=True)
            return
        
        if role not in interaction.guild.roles:
            await interaction.response.send_message("role not found in guild", ephemeral=True)
            return
        
        roles = confighandler.get_attribute("levels", fallback={})
        if level in roles:
            await interaction.response.send_message(f"level {level} already has a role assigned", ephemeral=True)
            return
        
        roles[level] = role.id
        confighandler.set_attribute("levels", roles)
        await interaction.response.send_message(f"set role {role.name} for level {level}", ephemeral=True)
        log(f"~2set level role {role.name} for level {level} in guild {interaction.guild.name}")

    @discord.app_commands.default_permissions(manage_roles=True)
    @discord.app_commands.command(name="unset_level_role", description="clear a level of rewards")
    async def unset_level_role(self, interaction: discord.Interaction, level: int):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1unset_level_role: could not find config handler for guild {interaction.guild.name}")
            return
        
        if level <= 1:
            await interaction.response.send_message("level must be greater than 1", ephemeral=True)
            return
        
        roles = confighandler.get_attribute("levels", fallback={})
        if level in roles:
            del roles[level]
            await interaction.response.send_message(f"level {level} has been cleared of reward", ephemeral=True)
            log(f"~2cleared level role for level {level} in guild {interaction.guild.name}")
            confighandler.set_attribute("levels", roles)
            return
        else:
            await interaction.response.send_message(f"that level doesn't have a role reward, so it couldn't be deleted.", ephemeral=True)
            log(f"~2tried to clear level role for level {level} in guild {interaction.guild.name}, but there was no role to clear.")
        
    @discord.app_commands.command(name="roles", description="get the list of role rewards for this server")
    async def roles(self, interaction: discord.Interaction):
        allowed_mentions = discord.AllowedMentions.none()
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1roles: could not find config handler for guild {interaction.guild.name}")
            await interaction.response.send_message("there was an error with this guild's confighandler", ephemeral=True, allowed_mentions=allowed_mentions)
            return

        roles = confighandler.get_attribute("levels", fallback={})
        if not roles:
            await interaction.response.send_message("no level role rewards are set for this server.", ephemeral=True, allowed_mentions=allowed_mentions)
            return

        lines = []
        for lvl, role_id in sorted(roles.items()):
            role = interaction.guild.get_role(role_id)
            if role:
                lines.append(f"level {lvl}: {role.mention}")
            else:
                lines.append(f"level {lvl}: (role not found, id: {role_id})")

        msg = "level role rewards for this server:\n" + "\n".join(lines)
        await interaction.response.send_message(msg, allowed_mentions=allowed_mentions)

    @discord.app_commands.default_permissions(manage_channels=True)
    @discord.app_commands.command(name="toggle_xp", description="toggle whether users can gain xp in a specific channel")
    async def toggle_xp_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1toggle_xp: could not find config handler for guild {interaction.guild.name}")
            await interaction.response.send_message("there was an error with this guild's confighandler", ephemeral=True)
            return

        disabled_channels = confighandler.get_attribute("disabled_channels", fallback=[])
        
        if channel.id in disabled_channels:
            disabled_channels.remove(channel.id)
            confighandler.set_attribute("disabled_channels", disabled_channels)
            await interaction.response.send_message(f"xp gain has been enabled in {channel.mention}")
            log(f"~2enabled xp gain in {channel.name} for guild {interaction.guild.name}")
        else:
            disabled_channels.append(channel.id)
            confighandler.set_attribute("disabled_channels", disabled_channels)
            await interaction.response.send_message(f"xp gain has been disabled in {channel.mention}")
            log(f"~2disabled xp gain in {channel.name} for guild {interaction.guild.name}")
        



    @discord.app_commands.command(name="rank", description="get your rank in the leaderboard.")
    async def rank(self, interaction: discord.Interaction, target: discord.Member=None):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1rank: could not find config handler for guild {interaction.guild.name}")
            await interaction.response.send_message("there was an error with this guild's confighandler", ephemeral=True)
            return
        
        if target is None:
            target = interaction.user
            self = True
        else:
            self = False

        theme = confighandler.get_attribute("colour", fallback=(40, 40, 40))

        leaderboard = lvbsc.format_leaderboard(
            guild_id=interaction.guild.id,
            confighandler=confighandler
        )

        user_id = target.id
        user_entry = None
        for entry in leaderboard:
            if entry[2] == user_id:
                user_entry = entry
                break

        

        if not user_entry:
            await interaction.response.send_message(f"{'you' if self else 'they'} are not on the leaderboard yet!", ephemeral=True)
            return

        image_path = lvimg.generate_rank_card_image(
            guild_id=interaction.guild.id,
            guild_name=interaction.guild.name,
            leaderboard=leaderboard,
            user_requested=user_id,
            theme=theme
        )

        if not image_path:
            await interaction.response.send_message("sorry, there was an error trying to generate your rank card.", ephemeral=True)
            return

        image_path = str(image_path)
        file = discord.File(image_path, filename="rank_card.png")

        await interaction.response.send_message(file=file)

    # TODO: make themes a proper config thing

    @discord.app_commands.command(name="leaderboard", description="get the leaderboard for the guild.")
    async def leaderboard(self, interaction: discord.Interaction, page:int=1):
        confighandler = self.confighandlers.get(interaction.guild.id, None)
        if confighandler is None:
            log(f"~1leaderboard: could not find config handler for guild {interaction.guild.name}")
            return
        theme = confighandler.get_attribute("colour", fallback=(40, 40, 40))

        if interaction.guild.icon is not None:
            guild_icon = await interaction.guild.icon.read()
        else:
            guild_icon = None

        leaderboard = lvbsc.format_leaderboard(
            guild_id=interaction.guild.id,
            confighandler=confighandler
        )

        image_path = lvimg.generate_leaderboard_image(
            guild_id=interaction.guild.id,
            guild_name=interaction.guild.name,
            leaderboard=leaderboard,
            max_rows=6,
            page_requested=page,
            theme=theme,
            icon=guild_icon
        )

        image_path = str(image_path)

        file = discord.File(image_path, filename="leaderboard.png")

        await interaction.response.send_message(file=file)

            


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))