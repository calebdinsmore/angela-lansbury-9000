from nextcord import slash_command, Permissions, Interaction, SlashOption
from nextcord.ext import commands, menus

from bot.cogs.server_admin import server_admin_helper, check_perms_view
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

    @server_admin.subcommand(name='check-perms', description='Check for potential permissions issues.')
    async def check_perms(self, interaction: Interaction):
        server_perms_description = server_admin_helper.check_perms(interaction.guild)
        server_perms_description = '\n'.join(server_perms_description)
        channel_entries = check_perms_view.get_channel_perm_entries(interaction.guild)
        source = check_perms_view.CheckPermsPageSource(channel_entries, server_perms_description)
        pages = menus.ButtonMenuPages(source=source, delete_message_after=True)
        await pages.start(interaction=interaction, ephemeral=True)
