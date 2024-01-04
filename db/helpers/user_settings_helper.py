from db import DB, UserSettings


def get_user_settings(user_id: int, guild_id: int):
    user_settings = DB.s.first(UserSettings, user_id=user_id, guild_id=guild_id)
    if user_settings is None:
        user_settings = UserSettings(user_id=user_id, guild_id=guild_id)
        DB.s.add(user_settings)
        DB.s.commit()
    return user_settings


def set_image_deletion_enabled(user_id: int, guild_id: int, enabled: bool):
    user_settings = get_user_settings(user_id, guild_id)
    user_settings.image_deletion_prompts_enabled = enabled
    DB.s.commit()
