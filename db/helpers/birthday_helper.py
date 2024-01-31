from typing import List, Tuple

from db import DB

import sqlalchemy as sa
import datetime as dt

from db.model.birthday import Birthday
from db.model.guild_config import GuildConfig


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


def update_settings(guild_id: int, channel_id: int):
    try:
        if not DB.s.first(GuildConfig, guild_id=guild_id):
            DB.s.add(GuildConfig(guild_id=guild_id,
                                 birthday_channel_id=channel_id))
        else:
            DB.s.execute(
                sa.update(GuildConfig)
                    .where(GuildConfig.guild_id == guild_id)
                    .values(birthday_channel_id=channel_id)
            )
        DB.s.commit()
        return True
    except:
        DB.s.rollback()
        return False


def get_birthday_channel_id(guild_id: int):
    guild_config = DB.s.first(GuildConfig, guild_id=guild_id)
    if guild_config:
        return guild_config.birthday_channel_id
    return None


def get_todays_birthdays() -> List[Birthday]:
    """
    Gets the birthdays for today
    :return: array of guild_ids with an array of Birthdays
    """
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    queried_birthdays = DB.s.execute(
        sa.text(f"""
        SELECT *
        FROM birthdays
        WHERE month = {now.month} and day = {now.day}
        ORDER BY guild_id desc;
        """)
    ).all()
    # make hashmap of guild_id -> [birthdays]
    birthdays = {guild_id: [] for guild_id in set([birthday.guild_id for birthday in queried_birthdays])}
    for birthday in queried_birthdays:
        birthdays[birthday.guild_id].append(birthday)
    return birthdays
