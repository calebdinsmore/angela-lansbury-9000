from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class GlobalLeaderboardGuild(DB.Model):
    guild_id: Mapped[int] = mapped_column(primary_key=True)
    leaderboard_name: Mapped[str] = mapped_column()
