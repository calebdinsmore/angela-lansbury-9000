import nextcord

from db import UserChannelSettings


class UserChannelConfigViewModel:
    def __init__(self, channel: nextcord.TextChannel | nextcord.Thread, db_model: 'UserChannelSettings'):
        self._channel = channel
        self._db_model = db_model

    @property
    def display(self):
        def days_to_string(days):
            if days is None:
                return 'Prompt'
            if days == 0:
                return '**Keep**'
            return f'**{days} days**' if days > 1 else '**1 day**'
        return f'{self._channel.mention}: ({days_to_string(self._db_model.delete_after)})'

    def bot_has_permissions(self, bot_member: nextcord.Member):
        channel_perms = self._channel.permissions_for(bot_member)
        checks = [
            channel_perms.manage_messages,
            channel_perms.read_message_history,
            channel_perms.send_messages
        ]
        return all(checks)


def compile_user_channel_config_view_models(db_models: list['UserChannelSettings'],
                                            guild: nextcord.Guild,
                                            channels: dict[int, nextcord.TextChannel]):
    models = []
    for model in db_models:
        if channels.get(model.channel_id) is None:
            channel = guild.get_channel_or_thread(model.channel_id)
            if channel:
                models.append(UserChannelConfigViewModel(channel, model))
        else:
            models.append(UserChannelConfigViewModel(channels.get(model.channel_id), model))
    return models
