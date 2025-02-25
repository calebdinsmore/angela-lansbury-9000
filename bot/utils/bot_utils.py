import nextcord.ext.commands


async def get_or_fetch_guild(bot: nextcord.ext.commands.Bot, guild_id: int):
    guild = bot.get_guild(guild_id)
    if guild is None:
        try:
            guild = await bot.fetch_guild(guild_id)
        except nextcord.NotFound:
            return None
    return guild


async def get_or_fetch_channel(bot: nextcord.ext.commands.Bot | nextcord.Guild, channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except nextcord.NotFound:
            return None
    return channel
