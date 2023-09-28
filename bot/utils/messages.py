import nextcord

INFO_COLOR = 3700200
ERROR_COLOR = 16725552
SUCCESS_COLOR = 32768


def info(message: str):
    return nextcord.Embed(color=INFO_COLOR, description=message)


def error(message: str):
    return nextcord.Embed(color=ERROR_COLOR, description=message)


def success(message: str):
    return nextcord.Embed(color=SUCCESS_COLOR, description=message)
