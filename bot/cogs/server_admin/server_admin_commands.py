import nextcord
from nextcord import slash_command, Permissions, Interaction, SlashOption
from nextcord.ext import commands

from bot.utils import messages
from db.helpers import guild_config_helper


class ServerAdminCommands(commands.Cog):
    @slash_command(name='server-admin',
                   description='Server admin commands.',
                   force_global=True,
                   default_member_permissions=Permissions(manage_guild=True))
    async def server_admin(self, interaction: Interaction):
        pass

    @server_admin.subcommand(name='toggle-image-prompts', description='Enable or disable image deletion prompts.')
    async def toggle_image_prompts(self, interaction: Interaction, enabled: str = SlashOption(name='enabled',
                                                                                              choices=['✅', '❌'])):
        enabled = enabled == '✅'
        guild_config_helper.update_guild_config(interaction.guild_id, image_deletion_prompts_enabled=enabled)
        confirmation_word = 'Enabled' if enabled else 'Disabled'
        await interaction.send(embed=messages.success(f'{confirmation_word} image prompts for this server.'),
                               ephemeral=True)

    @server_admin.subcommand(name='error-log-channel', description='Set the channel for error logs.')
    async def error_log_channel(self,
                                interaction: Interaction,
                                channel: nextcord.TextChannel = SlashOption(name='channel',
                                                                            description='Channel to set as the error '
                                                                                        'log channel.')):
        guild_config_helper.update_guild_config(interaction.guild_id, error_logging_channel_id=channel.id)
        await interaction.send(embed=messages.success(f'Successfully set the error log channel to {channel.mention}.'),
                               ephemeral=True)
