from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class GuildConfig(DB.Model):
    __tablename__ = 'guild_config'

    guild_id: Mapped[int] = mapped_column(primary_key=True)
    birthday_channel_id: Mapped[int] = mapped_column(nullable=True)
