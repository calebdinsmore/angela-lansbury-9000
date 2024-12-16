from typing import List

import nextcord.ui
import sentry_sdk

from bot.cogs.image_message_delete.views import util
from db.helpers import image_message_helper, user_settings_helper

PER_PAGE = 5


class ConfigurePromptsView(nextcord.ui.View):
    def __init__(self,
                 guild_id: int,
                 user: nextcord.Member,
                 text_channels: List[nextcord.TextChannel],
                 bot_user: nextcord.Member,
                 guild: nextcord.Guild):
        super().__init__()
        self.guild_id = guild_id
        self.user = user
        self.bot_user = bot_user
        self.user_id = user.id
        self.text_channels = text_channels
        self.guild = guild
        self.selected_channel_ids = []
        self.selected_setting = None
        self.user_settings = user_settings_helper.get_user_settings(self.user_id, guild_id)
        self.toggle_button.label = '✅ Image deletion enabled' if self.user_settings.image_deletion_prompts_enabled else '❌ Image deletion disabled'
        self._set_button_enabled()

    @property
    def image_deletion_enabled(self):
        return self.user_settings.image_deletion_prompts_enabled

    def generate_current_configuration_display(self):
        if not self.image_deletion_enabled:
            return 'Image deletion is disabled.'
        configs = self._get_current_configuration()
        if not configs:
            return '## No channel configurations set.'
        displays = []
        permission_issue = False
        for config in configs:
            if not config.bot_has_permissions(self.bot_user):
                permission_issue = True
                displays.append(f'- ~~{config.display}~~ ⚠️')
            else:
                displays.append(f'- {config.display}')
        permission_text = '-# A ⚠️ icon indicates that I do not have the required permissions to do image deletions in that channel.\n' if permission_issue else ''
        return '## Channel Configs\n' + '\n'.join(displays) + '\n' + permission_text

    @nextcord.ui.button(label='✅ Image deletion enabled', style=nextcord.ButtonStyle.primary)
    async def toggle_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.user_settings.image_deletion_prompts_enabled = not self.user_settings.image_deletion_prompts_enabled
        user_settings_helper.commit()
        self.toggle_button.label = '✅ Image deletion enabled' if self.user_settings.image_deletion_prompts_enabled else '❌ Image deletion disabled'
        self._set_button_enabled()
        await interaction.response.edit_message(view=self, content=self.generate_current_configuration_display())

    @nextcord.ui.channel_select(placeholder='Select channels to configure.',
                                channel_types=[nextcord.ChannelType.text,
                                               nextcord.ChannelType.public_thread,
                                               nextcord.ChannelType.private_thread],
                                min_values=1,
                                max_values=25)
    async def channel_select(self, _: nextcord.ui.Select, interaction: nextcord.Interaction):
        values: List[str] = interaction.data.get('values')
        self.selected_channel_ids = [int(value) for value in values]

    @nextcord.ui.string_select(placeholder='Select preferred image retention setting.',
                               options=[nextcord.SelectOption(label='Reset (prompt on each image)', value='prompt'),
                                        nextcord.SelectOption(label='Keep', value='keep'),
                                        nextcord.SelectOption(label='1 day', value='1'),
                                        nextcord.SelectOption(label='7 days', value='7'),
                                        nextcord.SelectOption(label='14 days', value='14'),
                                        nextcord.SelectOption(label='30 days', value='30'),
                                        ],
                               min_values=1,
                               max_values=1)
    async def retention_select(self, _: nextcord.ui.Select, interaction: nextcord.Interaction):
        values = interaction.data.get('values')
        if values:
            self.selected_setting = values[0]

    @nextcord.ui.button(label='Save Channels', style=nextcord.ButtonStyle.primary, row=4)
    async def save_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not self.selected_channel_ids or not self.selected_setting:
            await interaction.response.send_message('You must select a channel and setting.', ephemeral=True)
            return
        try:
            if self.selected_setting == 'prompt':
                image_message_helper.bulk_delete(interaction.guild_id, interaction.user.id, self.selected_channel_ids)
            else:
                value_to_days = {'keep': 0, '1': 1, '7': 7, '14': 14, '30': 30}
                image_message_helper.bulk_configure(interaction.guild_id,
                                                    interaction.user.id,
                                                    self.selected_channel_ids,
                                                    value_to_days[self.selected_setting])
        except Exception as e:
            await interaction.response.send_message(f'❌ Unable to configure due to an error. Try again later.',
                                                    ephemeral=True)
            sentry_sdk.capture_exception(e)
            return
        await interaction.response.edit_message(content=f'✅ Configuration saved!', view=None)
        self.stop()
        refreshed_view = ConfigurePromptsView(self.guild_id, self.user, self.text_channels, self.bot_user, self.guild)
        content = self.generate_current_configuration_display()
        await interaction.send(view=refreshed_view, content=content, ephemeral=True)

    @nextcord.ui.button(label='Close', style=nextcord.ButtonStyle.danger, row=4)
    async def close_button(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.stop()
        await interaction.response.edit_message(content='Closed.', view=None)

    def _get_current_configuration(self):
        configs = image_message_helper.get_all(self.guild_id, self.user_id)
        channel_dict = {channel.id: channel for channel in self.text_channels}
        return util.compile_user_channel_config_view_models(configs, self.guild, channel_dict)

    def _set_button_enabled(self):
        if not self.image_deletion_enabled:
            self.channel_select.disabled = True
            self.retention_select.disabled = True
            self.save_button.disabled = True
        else:
            self.channel_select.disabled = False
            self.retention_select.disabled = False
            self.save_button.disabled = False
