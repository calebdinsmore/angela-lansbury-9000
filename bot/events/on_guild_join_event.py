import nextcord
import sentry_sdk
from nextcord.ext import commands


def register_event(bot: commands.Bot):
    @bot.event
    async def on_guild_join(guild: nextcord.Guild):
        try:
            await guild.owner.send('👋 Thanks for adding me! If you have questions or concerns, or just want to be '
                                   'updated on new developments or issues, feel free to join '
                                   'https://discord.gg/NQm54zS82w')
        except Exception as e:
            sentry_sdk.capture_exception(e)
