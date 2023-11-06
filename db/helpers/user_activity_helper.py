from typing import List

import nextcord
import datetime as dt

from db import DB, UserActivity


def initialize_user_activity(members: List[nextcord.Member], guild_id: int):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    for member in members:
        if member.bot:
            continue
        if not DB.s.first(UserActivity, user_id=member.id):
            DB.s.add(UserActivity(user_id=member.id,
                                  guild_id=guild_id,
                                  tracking_started_on=now))
    DB.s.commit()


def get_or_create(user_id: int, guild_id: int):
    user_activity = DB.s.first(UserActivity, user_id=user_id, guild_id=guild_id)
    if user_activity is None:
        return setup_user(user_id, guild_id)
    return user_activity


def setup_user(user_id: int, guild_id: int):
    user_activity = DB.s.first(UserActivity, user_id=user_id, guild_id=guild_id)
    if user_activity:
        user_activity.reset()
    else:
        user_activity = UserActivity(user_id=user_id,
                                     guild_id=guild_id,
                                     tracking_started_on=dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc))
        DB.s.add(user_activity)
    DB.s.commit()
    return user_activity
