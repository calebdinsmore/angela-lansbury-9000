from db import DB, GuildConfig


def get_all_guild_configs():
    return DB.s.query(GuildConfig).all()


def get_guild_config(guild_id: int):
    config = DB.s.first(GuildConfig, guild_id=guild_id)
    if not config:
        config = GuildConfig(guild_id=guild_id)
        config.image_deletion_prompts_enabled = True
        DB.s.add(config)
        DB.s.commit()
    return config


def update_guild_config(guild_id: int, **kwargs):
    config = get_guild_config(guild_id)
    for k, v in kwargs.items():
        setattr(config, k, v)
    DB.s.commit()
    return config
