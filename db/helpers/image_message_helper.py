from typing import Dict

from db import DB
from db.model.user_channel_settings import UserChannelSettings


def get_user_channel_delete_settings(guild_id: int, channel_id: int, user_id: int):
    settings = DB.s.first(UserChannelSettings, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
    if not settings:
        return None
    return settings.delete_after


def change_user_channel_delete_settings(guild_id: int, channel_id: int, user_id: int, delete_after: int):
    settings = DB.s.first(UserChannelSettings, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
    if not settings:
        settings = UserChannelSettings(guild_id=guild_id, channel_id=channel_id, user_id=user_id,
                                       delete_after=delete_after)
    else:
        settings.delete_after = delete_after
    DB.s.add(settings)
    DB.s.commit()


def reset_user_channel_delete_settings(guild_id: int, channel_id: int, user_id: int):
    settings = DB.s.first(UserChannelSettings, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
    if settings:
        DB.s.delete(settings)
        DB.s.commit()
