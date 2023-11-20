import nextcord

from bot.config import Config
from bot.utils.constants import BUMPERS_GUILD_ID
from db.helpers import activity_module_settings_helper, rolling_message_log_helper


async def activity_handler(message: nextcord.Message):
    if message.author.bot:
        return
    if message.guild is None:
        return
    if Config().is_prod and message.guild.id != BUMPERS_GUILD_ID:
        return
    settings = activity_module_settings_helper.get_settings(message.guild.id)
    if message.channel.id in settings.excluded_channels:
        return

    rolling_message_log_helper.log_message(message.guild.id, message.author.id, message.id, message.created_at)
