import datetime
import enum
from typing import Set

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class ElfTier(enum.Enum):
    @classmethod
    def set(cls) -> Set['ElfTier']:
        return {ElfTier.bronze, ElfTier.silver, ElfTier.gold}

    bronze = 'bronze'
    silver = 'silver'
    gold = 'gold'


class GuildElf(DB.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(index=True)
    channel_id: Mapped[int] = mapped_column(index=True)
    message_id: Mapped[int] = mapped_column(nullable=True)
    tier: Mapped[Enum] = mapped_column(Enum(ElfTier), primary_key=True)
    drop_at: Mapped[datetime.datetime] = mapped_column()
    claimed: Mapped[bool] = mapped_column()
