from typing import List

from db import DB
from db.model.activity_role import ActivityRole


def get_activity_role(guild_id: int, role_id: int) -> ActivityRole:
    return DB.s.first(ActivityRole, guild_id=guild_id, role_id=role_id)


def get_activity_roles_by_guild_id() -> dict[int, List[ActivityRole]]:
    activity_roles: List[ActivityRole] = DB.s.all(ActivityRole)
    ar_dict = {}
    for ar in activity_roles:
        if ar.guild_id not in ar_dict:
            ar_dict[ar.guild_id] = []
        ar_dict[ar.guild_id].append(ar)
    return ar_dict


def save(activity_role: ActivityRole):
    if activity_role not in DB.s:
        DB.s.add(activity_role)
    DB.s.commit()


def delete(activity_role: ActivityRole):
    DB.s.delete(activity_role)
    DB.s.commit()
