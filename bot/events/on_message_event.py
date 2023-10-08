import nextcord
from nextcord.ext import commands

from bot.events.handlers.image_message_handler import image_message_handler


def register_event(bot: commands.Bot):
    @bot.event
    async def on_message(message: nextcord.Message):
        if message.author == bot.user:
            return

        await image_message_handler(message)
