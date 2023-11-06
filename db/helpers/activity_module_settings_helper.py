from typing import Dict

from db import DB
from db.helpers.activity_module_settings_wrapper import ActivityModuleSettingsWrapper
from db.model.activity_module_settings import ActivityModuleSettings


__CACHE: Dict[int, ActivityModuleSettingsWrapper] = {}


def get_settings(guild_id: int):
    if guild_id in __CACHE:
        return __CACHE[guild_id]
    settings = DB.s.first_or_create(ActivityModuleSettings, guild_id=guild_id)
    DB.s.commit()
    wrapper = ActivityModuleSettingsWrapper(settings)
    __CACHE[guild_id] = wrapper
    return wrapper
