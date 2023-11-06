from typing import List, Tuple

from db import DB

import sqlalchemy as sa
import datetime as dt

from db.model.rolling_message_log import RollingMessageLog


def get_inactive_users() -> List[Tuple[int, int]]:
    """
    Gets the user IDs for inactive users over the last month. It excludes users for whom tracking started within the
    last month
    :return: array of user IDs
    """
    results = DB.s.execute(
        sa.text("""
        SELECT author_id, rml.guild_id
        FROM rolling_message_log rml
        INNER JOIN user_activity ua on ua.user_id = rml.author_id 
        WHERE sent_at >= date('now', '-1 month') and ua.tracking_started_on <= date('now', '-1 month')
        GROUP BY author_id, rml.guild_id
        HAVING COUNT(*) < 5;
        """)
    ).all()
    return [(r[0], r[1]) for r in results]


def user_in_sixty_day_inactives(user_id: int, guild_id: int):
    results = DB.s.execute(
        sa.text("""
            SELECT author_id, rml.guild_id
            FROM rolling_message_log rml
            INNER JOIN user_activity ua on ua.user_id = rml.author_id 
            WHERE sent_at >= date('now', '-2 month') and ua.tracking_started_on <= date('now', '-2 month')
            GROUP BY author_id, rml.guild_id
            HAVING COUNT(*) < 5;
            """)
    ).all()
    results = [(r[0], r[1]) for r in results]
    for r in results:
        if r[0] == user_id and r[1] == guild_id:
            return True
    return False


def log_message(guild_id: int, author_id: int, message_id: int, sent_at: dt.datetime):
    DB.s.add(RollingMessageLog(guild_id=guild_id, message_id=message_id, author_id=author_id, sent_at=sent_at))
    DB.s.commit()


def purge_old_messages(days=365):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    one_month_ago = now - dt.timedelta(days=days)
    DB.s.execute(
        sa.delete(RollingMessageLog)
        .where(RollingMessageLog.sent_at < one_month_ago)
    )
    DB.s.commit()


def message_count_for_author(author_id: int, days=30):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    window_start = now - dt.timedelta(days=days)
    return DB.s.execute(
        sa.select(RollingMessageLog)
        .where(RollingMessageLog.author_id == author_id)
        .where(RollingMessageLog.sent_at > window_start)
    ).rowcount
