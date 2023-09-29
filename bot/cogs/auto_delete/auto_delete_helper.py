"""
Collection of helper functions used by AutoDeleteCommands
"""
from typing import List

import nextcord
import datetime as dt
from db import AutoDeleteChannelConfig, DB, AutoDeleteType


class ConfigNotFound(Exception):
    pass


async def fetch_anchor_message(channel: nextcord.TextChannel, config: AutoDeleteChannelConfig):
    """
    This function first attempts to fetch the anchor message for a channel config. If not found (i.e. it was deleted),
    it then tries to fetch the original_anchor_message that the bot posted when /auto-delete config was invoked.
    Failing that, it re-raises the exception.
    """
    try:
        anchor_message = await channel.fetch_message(config.anchor_message)
    except nextcord.NotFound:
        try:
            config.anchor_message = config.original_anchor_message
            DB.s.commit()
            anchor_message = await channel.fetch_message(config.original_anchor_message)
        except nextcord.NotFound:
            raise
    return anchor_message


def remove_channel_config(guild_id: int, channel_id: int):
    current_config: AutoDeleteChannelConfig = DB.s.first(AutoDeleteChannelConfig,
                                                         guild_id=guild_id,
                                                         channel_id=channel_id)
    if current_config is None:
        raise ConfigNotFound()
    DB.s.delete(current_config)
    DB.s.commit()


def message_has_image(message: nextcord.Message):
    attachments_has_image = next(filter(lambda a: 'image' in a.content_type, message.attachments), False)
    embeds_has_image = next(filter(lambda e: e.type == 'image', message.embeds), False)
    return attachments_has_image or embeds_has_image


def get_stale_messages(all_messages: [nextcord.Message], config: AutoDeleteChannelConfig):
    """
    Gets stale messages that should be deleted.
    Side effect: if there are messages that are stale but shouldn't be deleted (e.g. photo message when config
    is set to delete only text messages), the most recent among them is set to be the new anchor message.
    I should pull that side effect out, but I'm lazy, and this works.
    """
    stale_messages: List[nextcord.Message] = []
    for message in all_messages:
        delta = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - message.created_at
        minutes_elapsed = delta.seconds // 60
        if minutes_elapsed >= config.delete_after_minutes:
            stale_messages.append(message)
    if config.auto_delete_type == AutoDeleteType.all:
        return stale_messages
    elif config.auto_delete_type == AutoDeleteType.photo:
        messages_to_delete = [m for m in stale_messages if message_has_image(m)]
        clear_messages = [m for m in stale_messages if not message_has_image(m)]
        if clear_messages:
            config.anchor_message = clear_messages[-1].id
            DB.s.commit()
        return messages_to_delete
    else:
        # text
        messages_to_delete = [m for m in stale_messages if not message_has_image(m)]
        clear_messages = [m for m in stale_messages if message_has_image(m)]
        if clear_messages:
            config.anchor_message = clear_messages[-1].id
            DB.s.commit()
        return messages_to_delete
