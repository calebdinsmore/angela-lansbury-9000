from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class UserElfCounts(DB.Model):
    guild_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    bronze: Mapped[int] = mapped_column(default=0)
    silver: Mapped[int] = mapped_column(default=0)
    gold: Mapped[int] = mapped_column(default=0)
    points: Mapped[int] = mapped_column(default=0)
