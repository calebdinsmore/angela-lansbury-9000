import enum
from typing import Union

import nextcord
from nextcord.ext import commands

from db.helpers import activity_module_settings_helper, guild_config_helper

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
        self.guild_id = guild_id
        self.error_channel = None
        self.activity_channel = None
        self.guild_config = None
        if guild_id:
            self.guild_config = guild_config_helper.get_guild_config(guild_id=guild_id)
        if level == LoggingLevel.ACTIVITY and guild_id:
            settings = activity_module_settings_helper.get_settings(guild_id=guild_id)
            if settings.model.log_channel:
                self.activity_channel = bot.get_channel(settings.model.log_channel)

    async def activity(self, content: str):
        if self.activity_channel is None:
            settings = activity_module_settings_helper.get_settings(guild_id=self.guild_id)
            if settings.model.log_channel:
                self.activity_channel = self.bot.get_channel(settings.model.log_channel)
        if self.activity_channel is None:
            content += '\n(Attempted to log this to activity, but no channel was found.)'
            await self.general_channel.send(content)
            return

        await self.activity_channel.send(content)

    async def error(self, content: str):
        if not self.guild_id:
            return
        guild = self.bot.get_guild(self.guild_id)
        error_embed = nextcord.Embed(color=nextcord.Color.red(), description=content)
        if self.error_channel is None:
            channel_id = self.guild_config.error_logging_channel_id
            if channel_id:
                self.error_channel = self.bot.get_channel(channel_id)
            if self.error_channel is None:
                if guild.owner:
                    self.error_channel = guild.owner
                    error_embed.set_footer(text='Use /server-admin error-log-channel in your server to set a custom '
                                                'error log channel.')
        await self.error_channel.send(embed=error_embed)

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
