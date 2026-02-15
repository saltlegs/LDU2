import discord
from discord.ext import commands
from discord import app_commands

from components.function.logging import log
from components.function.msgformat import format_msg
from components.function.moderation.basic import gen_case, get_case_embed
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

        await interaction.response.defer()

        this_case_id, this_case = gen_case(
            confighandler=config,
            case_type="note",
            case_target=interaction.user,
            case_author=self.bot.user,
            case_note="this is the test infraction",
            case_duration_seconds=600,
        )

        embed = await get_case_embed(self.bot, this_case_id, this_case)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationBeta(bot))