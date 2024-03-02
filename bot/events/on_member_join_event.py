import nextcord
from nextcord.ext import commands

from bot.utils.constants import BUMPERS_GUILD_ID
from db.helpers import user_activity_helper


def register_event(bot: commands.Bot):
    @bot.event
    async def on_member_join(member: nextcord.Member):
        if member.bot:
            return
        if member.guild.id != BUMPERS_GUILD_ID:
            return

        user_activity_helper.setup_user(member.id, member.guild.id)
