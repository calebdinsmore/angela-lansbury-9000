from typing import List, Tuple

from db import DB

import sqlalchemy as sa
import datetime as dt
import calendar
import sentry_sdk

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


def update_birthday_channel_settings(guild_id: int, channel_id: int):
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


def update_baby_month_channel_settings(guild_id: int, channel_id: int):
    try:
        if not DB.s.first(GuildConfig, guild_id=guild_id):
            DB.s.add(GuildConfig(guild_id=guild_id,
                                 baby_month_milestone_channel_id=channel_id))
        else:
            DB.s.execute(
                sa.update(GuildConfig)
                    .where(GuildConfig.guild_id == guild_id)
                    .values(baby_month_milestone_channel_id=channel_id)
            )
        DB.s.commit()
        return True
    except Exception as e:
        sentry_sdk.capture_exception(e)
        DB.s.rollback()
        return False


def get_birthday_channel_id(guild_id: int):
    guild_config = DB.s.first(GuildConfig, guild_id=guild_id)
    if guild_config:
        return guild_config.birthday_channel_id
    return None


def get_baby_month_milestone_channel_id(guild_id: int):
    guild_config = DB.s.first(GuildConfig, guild_id=guild_id)
    if guild_config:
        return guild_config.baby_month_milestone_channel_id
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


def is_last_day_of_month() -> bool:
    now = dt.datetime.utcnow()
    return now.day == calendar.monthrange(now.year, now.month)[1]


def get_todays_baby_month_milestones() -> List[Birthday]:
    """
    Gets the babies born on this day or the month for the last 12 months
    :return: array of guild_ids with an array of Birthdays
    """
    last_year = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - dt.timedelta(days=365)
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    queried_birthdays = DB.s.execute(
        sa.text(f"""
        SELECT *
        FROM birthdays
        WHERE day = {now.day} and ((year = {now.year} and month < {now.month}) or (year = {last_year.year} and month >= {now.month}))
        ORDER BY guild_id desc;
        """)
    ).all()
    last_day_of_month = is_last_day_of_month()
    if last_day_of_month:
        queried_birthdays += DB.s.execute(
            sa.text(f"""
            SELECT *
            FROM birthdays
            WHERE day > {now.day} and ((year = {now.year} and month < {now.month}) or (year = {last_year.year} and month >= {now.month}))
            ORDER BY guild_id desc;
            """)
        ).all()
        # make hashmap of guild_id -> [birthdays]
    birthdays = {guild_id: [] for guild_id in set([birthday.guild_id for birthday in queried_birthdays])}
    for birthday in queried_birthdays:
        birthdays[birthday.guild_id].append(birthday)
    return birthdays


def get_upcoming_birthdays(guild_id: int):
    # Get birthdays for this guild in the next month
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    next_month = now.month + 1
    if next_month > 12:
        next_month -= 12
    queried_birthdays = DB.s.execute(
        sa.text(f"""
        SELECT *
        FROM birthdays
        WHERE guild_id = {guild_id} and ((day > {now.day} and month = {now.month}) or (day <= {now.day} and month = {next_month}))
        ORDER BY month, day;
        """)
    ).all()
    return queried_birthdays
