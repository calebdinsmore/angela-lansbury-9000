import nextcord
from nextcord.ext import commands

from bot.utils.logger import get_logger, LoggingLevel
from db.helpers import activity_module_settings_helper


async def register_event(bot: commands.Bot):
    @bot.event
    async def on_member_update(before: nextcord.Member, after: nextcord.Member):
        settings = activity_module_settings_helper.get_settings(before.guild.id)
        if settings.model.inactive_role_id is None:
            return

        if nextcord.utils.get(before.roles, id=settings.model.inactive_role_id):
            if nextcord.utils.get(after.roles, id=settings.model.inactive_role_id) is None:
                # User was inactive, but now is active
                logger = get_logger(LoggingLevel.ACTIVITY, before.guild.id)
                await logger.log(f'{after.mention} just had their inactive role removed. Friendly reminder to reactivate '
                                 f'them using `/activity reactivate-member <member>` if they are no longer inactive.')
