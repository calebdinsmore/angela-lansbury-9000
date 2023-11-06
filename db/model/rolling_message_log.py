from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class RollingMessageLog(DB.Model):
    __tablename__ = 'rolling_message_log'

    message_id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(index=True)
    author_id: Mapped[int] = mapped_column(index=True)
    sent_at: Mapped[datetime] = mapped_column()
