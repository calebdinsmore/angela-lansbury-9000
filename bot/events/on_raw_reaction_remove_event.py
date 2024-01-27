import nextcord
from nextcord.ext import commands

from bot.events.handlers import temp_discussion_handler


def register_event(bot: commands.Bot):
    @bot.event
    async def on_raw_reaction_remove(payload: nextcord.RawReactionActionEvent):
        await temp_discussion_handler.handle_closure_react(bot, payload)
