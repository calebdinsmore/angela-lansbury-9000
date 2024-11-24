import nextcord.ui

from db.helpers import image_message_helper


class DeleteConfirmationView(nextcord.ui.View):
    def __init__(self, days: int, channel_id: int, guild_id: int, user_id: int):
        super().__init__()
        self.days = days
        self.days_label = f'{days}d' if days != 0 else 'Keep'
        button_label = f'Set channel default to {self.days_label}?'
        self.set_default.label = button_label
        self.guild_id = guild_id
        self.user_id = user_id
        self.channel_id = channel_id

    @nextcord.ui.button(style=nextcord.ButtonStyle.gray)
    async def set_default(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        image_message_helper.change_user_channel_delete_settings(self.guild_id,
                                                                 self.channel_id,
                                                                 self.user_id,
                                                                 self.days)
        action_description = ''
        if self.days == 0:
            action_description = "From now on, images you send in this channel will not be deleted by default, and I " \
                                 "won't prompt you about them."
        else:
            action_description = "From now on, images you send in this channel will be automatically be deleted after " \
                                 f"{self.days} day{'s' if self.days != 1 else ''}, and I won't prompt you about them."
        await interaction.response.edit_message(content=f'Channel default updated to {self.days_label}. '
                                                        f'{action_description}\n'
                                                        '-# To change your channel deletion settings, use '
                                                        '</image-prompts configure:1192657402617675907>',
                                                        view=None)
        self.stop()
