from typing import List, Tuple

from db import DB

import sqlalchemy as sa
import datetime as dt

from db.model.birthday import Birthday

def add_birthday(guild_id: int, user_id: int, name: str, month: int, day: int, year: int):
    try:
        DB.s.add(Birthday(guild_id=guild_id, user_id=user_id, name=name, month=month, day=day, year=year))
        DB.s.commit()
        return True
    except sa.exc.IntegrityError:
        DB.s.rollback()
        return False

def list_birthdays(guild_id: int, user_id: int):
    return DB.s.execute(
        sa.select(Birthday)
        .where(Birthday.guild_id == guild_id)
        .where(Birthday.user_id == user_id)
    ).all()

def delete_birthday(guild_id: int, user_id: int, name: str):
    try:
        DB.s.execute(
            sa.delete(Birthday)
            .where(Birthday.guild_id == guild_id)
            .where(Birthday.user_id == user_id)
            .where(Birthday.name == name)
        )
        DB.s.commit()
        return True
    except:
        DB.s.rollback()
        return False
