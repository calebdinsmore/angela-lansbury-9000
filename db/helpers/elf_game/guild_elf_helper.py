import datetime
from typing import List

from db import DB
from db.model.elf_game.guild_elf import GuildElf, ElfTier


def get_needed_tiers_for_guild(guild_id: int):
    unclaimed_elves: List[GuildElf] = DB.s.query(GuildElf)\
        .filter(GuildElf.guild_id == guild_id, GuildElf.claimed.is_(False))\
        .all()
    return list(ElfTier.set() - {elf.tier for elf in unclaimed_elves})


def add_guild_elf(guild_id: int, channel_id: int, tier: ElfTier, drop_at: datetime.datetime, message_id: int = None):
    elf = GuildElf(guild_id=guild_id,
                   channel_id=channel_id,
                   tier=tier,
                   drop_at=drop_at,
                   message_id=message_id,
                   claimed=False)
    DB.s.add(elf)
    DB.s.commit()
    return elf


