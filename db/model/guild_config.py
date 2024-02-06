from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class GuildConfig(DB.Model):
    __tablename__ = 'guild_config'

    guild_id: Mapped[int] = mapped_column(primary_key=True)
    birthday_channel_id: Mapped[int] = mapped_column(nullable=True)
    image_deletion_prompts_enabled: Mapped[bool] = mapped_column(nullable=True)
    error_logging_channel_id: Mapped[int] = mapped_column(nullable=True)
