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
    results = DB.s.execute(
        sa.text("""
        SELECT name, month, day, year
        FROM birthdays
        WHERE guild_id = :guild_id AND user_id = :user_id
        """)
    ).all()
    return [(r[0], r[1], r[2], r[3]) for r in results]

def delete_birthday(guild_id: int, user_id: int, name: str):
    DB.s.execute(
        sa.delete(Birthday)
        .where(Birthday.guild_id == guild_id and Birthday.user_id == user_id and Birthday.name == name)
    )
    DB.s.commit()
