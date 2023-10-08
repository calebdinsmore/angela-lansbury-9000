import nextcord

INFO_COLOR = 3700200
ERROR_COLOR = 16725552
SUCCESS_COLOR = 32768


def message_has_image(message: nextcord.Message):
    attachments_has_image = next(filter(lambda a: 'image' in a.content_type, message.attachments), False)
    attachments_has_video = next(filter(lambda a: 'video' in a.content_type, message.attachments), False)
    embeds_has_image = next(filter(lambda e: e.type == 'image', message.embeds), False)
    embeds_has_video = next(filter(lambda e: e.type == 'video', message.embeds), False)
    return attachments_has_image or attachments_has_video or embeds_has_image or embeds_has_video


def info(message: str):
    return nextcord.Embed(color=INFO_COLOR, description=message)


def error(message: str):
    return nextcord.Embed(color=ERROR_COLOR, description=message)


def success(message: str):
    return nextcord.Embed(color=SUCCESS_COLOR, description=message)
