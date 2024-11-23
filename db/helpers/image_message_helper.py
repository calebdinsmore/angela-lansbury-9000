from typing import Dict, List

from db import DB
from db.model.user_channel_settings import UserChannelSettings


def get_all(guild_id: int, user_id: int) -> List[UserChannelSettings]:
    return DB.s.all(UserChannelSettings, guild_id=guild_id, user_id=user_id)


def bulk_delete(guild_id: int, user_id: int, channel_ids: List[int]):
    DB.s.query(UserChannelSettings).filter(UserChannelSettings.guild_id == guild_id,
                                           UserChannelSettings.user_id == user_id,
                                           UserChannelSettings.channel_id.in_(channel_ids)).delete(synchronize_session=False)
    DB.s.commit()


def bulk_configure(guild_id: int, user_id: int, channel_ids: List[int], delete_after: int):
    current_settings = {settings.channel_id: settings for settings in get_all(guild_id, user_id)}
    for channel_id in channel_ids:
        if channel_id in current_settings:
            current_settings[channel_id].delete_after = delete_after
        else:
            DB.s.add(UserChannelSettings(guild_id=guild_id, user_id=user_id, channel_id=channel_id, delete_after=delete_after))
    DB.s.commit()


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
