from typing import List, Tuple

from sqlalchemy import func

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
        SELECT ua.user_id , ua.guild_id
        FROM user_activity ua
        LEFT JOIN (
            SELECT rml.author_id as author_id, COUNT(*) as message_count
            FROM rolling_message_log rml
            WHERE sent_at >= date('now', '-1 month')
            GROUP BY rml.author_id
        ) AS user_messages ON ua.user_id = user_messages.author_id
        WHERE ua.is_active 
        and ua.tracking_started_on <= date('now', '-1 month') 
        and (user_messages.message_count < 5 
            or user_messages.message_count IS NULL);
        """)
    ).all()
    return [(r[0], r[1]) for r in results]


def user_in_sixty_day_inactives(user_id: int, guild_id: int):
    results = DB.s.execute(
        sa.text("""
            SELECT ua.user_id , ua.guild_id
            FROM user_activity ua
            LEFT JOIN (
                SELECT rml.author_id as author_id, COUNT(*) as message_count
                FROM rolling_message_log rml
                WHERE sent_at >= date('now', '-2 month')
                GROUP BY rml.author_id
            ) AS user_messages ON ua.user_id = user_messages.author_id
            WHERE ua.is_active 
            and ua.tracking_started_on <= date('now', '-2 month') 
            and (user_messages.message_count < 5 
                or user_messages.message_count IS NULL);
            """)
    ).all()
    results = [(r[0], r[1]) for r in results]
    for r in results:
        if r[0] == user_id and r[1] == guild_id:
            return True
    return False


def get_all_ninety_day_stats(guild_id: int) -> List[Tuple[int, int]]:
    results = DB.s.execute(
        sa.text("""
        SELECT 
            author_id,
            COUNT(message_id) / 3 AS rolling_monthly_average
        FROM 
            rolling_message_log
        WHERE 
            sent_at >= date('now', '-90 days') and guild_id = :guild_id
        GROUP BY 
            author_id
        ORDER BY
            rolling_monthly_average DESC;
        """),
        {"guild_id": guild_id}
    ).all()
    results = [(r[0], r[1]) for r in results]
    return results


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


def message_count_for_author(author_id: int, guild_id: int, days=30, divisor=1):
    results = DB.s.execute(
        sa.text(f"""
            SELECT 
                COUNT(message_id) / {divisor} AS rolling_monthly_average
            FROM 
                rolling_message_log
            WHERE 
                sent_at >= date('now', '-{days} days') and guild_id = :guild_id and author_id = :author_id
            GROUP BY 
                author_id
            ORDER BY
                rolling_monthly_average DESC;
            """),
        {"guild_id": guild_id, "author_id": author_id}
    ).first()
    return results[0] if results else 0
