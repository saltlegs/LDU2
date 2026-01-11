import discord
from discord.ext import commands
from discord import app_commands

from components.function.logging import log
from components.function.msgformat import format_msg
from components.classes.confighandler import ConfigHandler, register_config


class WelcomeCog(commands.Cog): 

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        register_config("welcome_config")
        self.generate_handlers()

    def generate_handlers(self):
        self.confighandlers = {}
        guilds = self.bot.guilds
        for guild in guilds:
            confighandler = ConfigHandler("welcome_config", guild)
            confighandler.load_config()
            self.confighandlers[guild.id] = confighandler

    def get_config(self, guild_id: int) -> ConfigHandler:
        if guild_id not in self.confighandlers:
            guild = self.bot.get_guild(guild_id)
            if guild:
                confighandler = ConfigHandler("welcome_config", guild)
                confighandler.load_config()
                self.confighandlers[guild_id] = confighandler
        return self.confighandlers.get(guild_id)

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        config = self.get_config(guild.id)

        notifchannel = config.get_attribute("notifchannel", None)
        if notifchannel:
            notifchannel = guild.get_channel(int(notifchannel))
        else: 
            return

        if not notifchannel:
            log(f"~3join channel not found in {guild.name}")
            return

        permissions = notifchannel.permissions_for(guild.me)
        if not permissions.send_messages:
            log(f"~1no send permissions in {notifchannel.name} in {guild.name}")
            return

        joinmsg = config.get_attribute("joinmsg", None)
        if joinmsg:
            try:
                joinmsg = format_msg(joinmsg, guild, member)
                await notifchannel.send(joinmsg)
                log(f"~2sent join msg for {member.name} in {guild.name}")
            except Exception as e:
                log(f"~1failed to send join msg in {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        config = self.get_config(guild.id)

        notifchannel = config.get_attribute("notifchannel", None)
        if notifchannel:
            notifchannel = guild.get_channel(int(notifchannel))
        else: 
            return

        if not notifchannel:
            log(f"~3leave channel not found in {guild.name}")
            return

        permissions = notifchannel.permissions_for(guild.me)
        if not permissions.send_messages:
            log(f"~1no send permissions in {notifchannel.name} in {guild.name}")
            return

        leavemsg = config.get_attribute("leavemsg", None)
        if leavemsg:
            try:
                leavemsg = format_msg(leavemsg, guild, member)
                await notifchannel.send(leavemsg)
                log(f"~2sent leave msg for {member.name} in {guild.name}")
            except Exception as e:
                log(f"~1failed to send leave msg in {guild.name}: {e}")

    @app_commands.command(name="set_welcome_channel", description="set the channel where join/leave messages are sent")
    @app_commands.default_permissions(manage_channels=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = self.get_config(interaction.guild.id)
        permissions = channel.permissions_for(interaction.guild.me)
        can_send = permissions.send_messages

        if not can_send:
            await interaction.response.send_message("i can't send messages there!", ephemeral=True)
            return

        config.set_attribute("notifchannel", channel.id)

        await interaction.response.send_message(f"welcome channel set to {channel.mention}!")
        log(f"~2set welcome channel to {channel.name} in {interaction.guild.name}")

    @app_commands.command(name="disable_welcome_channel", description="disable welcome messages")
    @app_commands.default_permissions(manage_channels=True)
    async def disable_welcome_channel(self, interaction: discord.Interaction):
        config = self.get_config(interaction.guild.id)
        old_channel_id = config.get_attribute("notifchannel", None)
        
        if not old_channel_id:
            await interaction.response.send_message("welcome messages are already disabled!", ephemeral=True)
            return
        
        config.set_attribute("notifchannel", None)
        await interaction.response.send_message("welcome messages disabled!")
        log(f"~2disabled welcome channel in {interaction.guild.name}")

    @app_commands.command(name="set_join_message", description="set the message sent to join users")
    @app_commands.default_permissions(manage_channels=True)
    async def set_join_message(self, interaction: discord.Interaction, message: str):
        config = self.get_config(interaction.guild.id)
        guild = interaction.guild
        invoker = interaction.user

        nomentions = discord.AllowedMentions.none()

        try:
            message_formatted = format_msg(message, guild, invoker)
            old_message = config.get_attribute("joinmsg")
            config.set_attribute("joinmsg", message)

            bot_response = (
                f"your new join message has been set to:\n\n"
                f"`{message}`\n\n"
                f"here's what it looks formatted as an example:\n\n"
                f"{message_formatted}\n\n"
                f"your old join message was:\n\n"
                f"`{old_message}`"
            )  
            await interaction.response.send_message(bot_response, allowed_mentions=nomentions)
            log(f"set new join msg {message} in {guild.name}")
        except Exception as e:
            await interaction.response.send_message("something went wrong :(", ephemeral=True)
            log(f"failed to set new join msg {message} in {guild.name}: {e}")

    @app_commands.command(name="set_leave_message", description="set the message sent to leaving users")
    @app_commands.default_permissions(manage_channels=True)
    async def set_leave_message(self, interaction: discord.Interaction, message: str):
        config = self.get_config(interaction.guild.id)
        guild = interaction.guild
        invoker = interaction.user

        nomentions = discord.AllowedMentions.none()

        try:
            message_formatted = format_msg(message, guild, invoker)
            old_message = config.get_attribute("leavemsg")
            config.set_attribute("leavemsg", message)

            bot_response = (
                f"your new leave message has been set to:\n\n"
                f"`{message}`\n\n"
                f"here's what it looks formatted as an example:\n\n"
                f"{message_formatted}\n\n"
                f"your old leave message was:\n\n"
                f"`{old_message}`"
            )  
            await interaction.response.send_message(bot_response, allowed_mentions=nomentions)
            log(f"set new leave msg {message} in {guild.name}")
        except Exception as e:
            await interaction.response.send_message("something went wrong :(", ephemeral=True)
            log(f"failed to set new leave msg {message} in {guild.name}: {e}")

    @app_commands.command(name="welcome_test", description="test welcome and leave messages")
    @app_commands.default_permissions(manage_channels=True)
    async def welcome_test(self, interaction: discord.Interaction):
        invoker = interaction.user

        await self.on_member_join(invoker)
        await self.on_member_remove(invoker)

        await interaction.response.send_message("test messages sent!", ephemeral=True)

        


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))