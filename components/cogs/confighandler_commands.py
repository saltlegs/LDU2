import discord
from discord import app_commands
from discord.ext import commands
import yaml

from components.shared_instances import shcogs
from components.function.logging import log
from components.function.api_shorthand import sync_cogs_for_guild
from components.function.savedata import get_guild_attribute, set_guild_attribute
from components.classes.confighandler import ConfigHandler, register_config, COG_LABELS

class ConfigHandlerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

class ConfigHandlerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="toggle_module")
    @discord.app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        module="name of the module to toggle (enable/disable)"
    )
    async def toggle_module(self, interaction: discord.Interaction, module: str):
        disabled = get_guild_attribute(interaction.guild.id, "disabled_cogs") or []

        if module not in shcogs:
            await interaction.response.send_message(
                f"no module named '{module}' found.",
                ephemeral=False
            )
            return

        action = ""
        if module in disabled:
            disabled.remove(module)
            action = "enabled"
            action_verb = "enabling"
        else:
            disabled.append(module)
            action = "disabled"
            action_verb = "disabling"

        await interaction.response.send_message(
            f"{action_verb} {module} module, this might take a few moments for discord to let us register this change...",
            ephemeral=False
        )
        msg = await interaction.original_response()

        set_guild_attribute(interaction.guild.id, "disabled_cogs", disabled)
        await sync_cogs_for_guild(interaction.client, interaction.client.tree, interaction.guild)
        log(f"{action} {module} module for server {interaction.guild.name}")

        await msg.reply(
            f"{module} module has been {action}! the change may not show up visually until discord is restarted (ctrl+r/⌘+r on desktop, close & open the app on mobile)."
        )

    @toggle_module.autocomplete('module')
    async def toggle_module_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = []
        seen = set()
        for c in shcogs:
            if c in seen:
                continue
            seen.add(c)
            if current.lower() in c.lower() and c != "ConfigHandlerCommands":
                choices.append(c)
        return [app_commands.Choice(name=c, value=c) for c in choices[:25]]

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigHandlerCommands(bot))
