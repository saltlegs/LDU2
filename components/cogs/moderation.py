import discord
from discord.ext import commands
from discord import app_commands

from components.function.logging import log
from components.function.msgformat import format_msg
from components.function.moderation.basic import gen_case, get_case_embed, make_simple_embed, str_to_seconds
from components.function.api_shorthand import is_user_banned
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

    @app_commands.default_permissions(discord.Permissions(administrator=True))
    @app_commands.command(name="note", description="add a note onto a user")
    @app_commands.default_permissions(manage_messages=True)
    async def set_log_channel(self, interaction: discord.Interaction, channel:discord.TextChannel):
        config = self.get_config(interaction.guild.id)

        config.set_attribute("moderation_log_channel", channel.id)

        await interaction.response.send_message(embed=make_simple_embed(f"set channel: {channel.mention}"), ephemeral=True)

    @app_commands.default_permissions(discord.Permissions(manage_roles=True))
    @app_commands.command(name="note", description="add a note onto a user")
    @app_commands.default_permissions(manage_messages=True)
    async def note(self, interaction: discord.Interaction, target:discord.Member, comment:str):
        config = self.get_config(interaction.guild.id)

        this_case_id, this_case = gen_case(
            confighandler=config,
            case_type="note",
            case_target=target,
            case_author=interaction.user,
            case_note=comment,
        )

        await interaction.response.send_message(embed=make_simple_embed(f"note added: {comment}"), ephemeral=True)

    @app_commands.default_permissions(discord.Permissions(ban_members=True))
    @app_commands.command(name="ban", description="ban a user")
    @app_commands.default_permissions(manage_messages=True)
    async def note(self, interaction: discord.Interaction, target:discord.Member, duration:str, comment:str):
        config = self.get_config(interaction.guild.id)

        await interaction.response.defer()

        try:
            banned_already = await is_user_banned(target.id, interaction.guild.id)
            if banned_already: 
                await interaction.followup.send(embed=make_simple_embed(f"user is already banned!"))
                return
        except discord.NotFound:    pass
        except ValueError:          pass

        try:
            duration_seconds = str_to_seconds(duration)
        except ValueError as e:
            await interaction.followup.send(embed=make_simple_embed(f"error", desc=e), ephemeral=True)
            return
        
        try:
            await interaction.guild.ban(
                user=target,
                reason=comment,
                delete_message_days=0,
                delete_message_seconds=0,
            )
        except discord.Forbidden:
            await interaction.followup.send(embed=make_simple_embed(f"error", desc=f"i don't have permission to ban that user."), ephemeral=True)
            return
        except discord.NotFound:
            await interaction.followup.send(embed=make_simple_embed(f"error", desc=f"i can't find that user."), ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(embed=make_simple_embed(f"error", desc=f"something went wrong with the discord API"), ephemeral=True)
            return

        this_case_id, this_case = gen_case(
            confighandler=config,
            case_type="ban",
            case_target=target,
            case_author=interaction.user,
            case_note=comment,
            case_duration_seconds=duration_seconds
        )

        case_embed = await get_case_embed(self.bot, this_case_id, this_case)
        log_channel_id = config.get_attribute("moderation_log_channel")
        log_channel = self.bot.get_channel(log_channel_id)

        if log_channel:
            await log_channel.send(embed=case_embed)

        await interaction.followup.send(embed=make_simple_embed(f"banned user: {comment}"))


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationBeta(bot))