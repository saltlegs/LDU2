import discord
from discord.ext import commands
import yaml

from components.function.logging import log
from components.classes.confighandler import ConfigHandler, register_config, COG_LABELS

class ConfigHandlerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @discord.app_commands.command(name="list_configs", description="list all registered configs")
    # async def list_configs(self, interaction: discord.Interaction):
    #     if not COG_LABELS:
    #         await interaction.response.send_message("No configs are registered.", ephemeral=True)
    #         return
    #     config_list = '\n'.join(f"- {name}" for name in COG_LABELS)
    #     await interaction.response.send_message(f"registered configs:\n```{config_list}```", ephemeral=True)

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     log("~2loaded config handler commands")

    # @discord.app_commands.command(name="get_config", description="get a config")
    # async def get_config(self, interaction: discord.Interaction, config_name: str):
    #     if config_name not in COG_LABELS:
    #         await interaction.response.send_message(f"config {config_name} is not registered", ephemeral=True)
    #         return
    #     guild = interaction.guild
    #     confighandler = ConfigHandler(config_name, guild)
    #     confighandler.load_config()
    #     config = confighandler.config

    #     config_pretty = yaml.dump(config, sort_keys=False, indent=4, allow_unicode=True, width=500)
    #     config_pretty = f"```yaml\n{config_pretty}```"
    #     await interaction.response.send_message(f"config for {guild.name}: {config_pretty}")

    


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigHandlerCommands(bot))