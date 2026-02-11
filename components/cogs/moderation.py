import discord
from discord.ext import commands
from discord import app_commands

from components.function.logging import log
from components.function.msgformat import format_msg
from components.classes.confighandler import ConfigHandler, register_config


class ModerationBeta(commands.Cog): 

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        register_config("moderation_config")
        self.generate_handlers()

    def generate_handlers(self):
        self.confighandlers = {}
        guilds = self.bot.guilds
        for guild in guilds:
            confighandler = ConfigHandler("moderation_config", guild)
            confighandler.load_config()
            self.confighandlers[guild.id] = confighandler

    def get_config(self, guild_id: int) -> ConfigHandler:
        if guild_id not in self.confighandlers:
            guild = self.bot.get_guild(guild_id)
            if guild:
                confighandler = ConfigHandler("moderation_config", guild)
                confighandler.load_config()
                self.confighandlers[guild_id] = confighandler
        return self.confighandlers.get(guild_id)

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @app_commands.command(name="infraction", description="dummy infraction command")
    @app_commands.default_permissions(manage_channels=True)
    async def infraction(self, interaction: discord.Interaction):
        config = self.get_config(interaction.guild.id)

        interaction.response.send_message("test")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationBeta(bot))