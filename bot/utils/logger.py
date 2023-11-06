import enum
from typing import Union, Optional

from nextcord.ext import commands

from bot.utils.constants import BUMPERS_GUILD_ID
from db.helpers import activity_module_settings_helper

BOT: Union[commands.Bot, None] = None
BUMPERS_LOG_CHANNEL = 1171120556972724245


class LoggingLevel(enum.Enum):
    ACTIVITY = 'activity'
    GENERAL = 'general'


class Logger:
    def __init__(self, level: LoggingLevel, bot: commands.Bot, guild_id: int = None):
        self.level = level
        self.bot = bot
        self.general_channel = bot.get_channel(BUMPERS_LOG_CHANNEL)
        self.activity_channel = None
        if level == LoggingLevel.ACTIVITY and guild_id:
            settings = activity_module_settings_helper.get_settings(guild_id=guild_id)
            if settings.model.log_channel:
                self.activity_channel = bot.get_channel(settings.model.log_channel)

    async def log(self, content: str):
        if self.level == LoggingLevel.ACTIVITY:
            if self.activity_channel is None:
                content += '\n(Attempted to log this to activity, but no channel was found.)'
            else:
                await self.activity_channel.send(content)
        await self.general_channel.send(content)


def register_bot(bot: commands.Bot):
    global BOT
    BOT = bot


def get_logger(logging_level: LoggingLevel, guild_id: int = None):
    global BOT
    if BOT is None:
        raise RuntimeError('BOT has not been registered')
    return Logger(logging_level, BOT, guild_id)
