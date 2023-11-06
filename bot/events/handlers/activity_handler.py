import nextcord

from db.helpers import activity_module_settings_helper, rolling_message_log_helper


async def activity_handler(message: nextcord.Message):
    if message.author.bot:
        return
    settings = activity_module_settings_helper.get_settings(message.guild.id)
    if message.channel.id in settings.excluded_channels:
        return

    rolling_message_log_helper.log_message(message.guild.id, message.author.id, message.id, message.created_at)
