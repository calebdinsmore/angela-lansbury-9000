import nextcord
import random

from db.model.birthday import Birthday

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


def santa_message(message: str, sender: nextcord.User, show_name=False):
    embed = nextcord.Embed(description=message)
    name = sender.name if show_name else 'Message from your Santa!'
    icon_url = sender.avatar.url if sender.avatar and show_name else None
    embed.set_author(name=name, icon_url=icon_url)
    return embed


def get_random_angela_gif():
    angela_gifs = [
        "https://media.giphy.com/media/MF41YrnoSgZEY/giphy.gif",
        "https://media.giphy.com/media/3ohs4kPMizP0sn727e/giphy.gif",
        "https://media.giphy.com/media/26gspGYxmtaUUTq7u/giphy.gif",
        "https://media.giphy.com/media/l0ExghDSRxU2g55sc/giphy.gif",
        "https://media.giphy.com/media/l0ExiVMKsnIy0tzBC/giphy.gif",
        "https://media.giphy.com/media/36fSgmwvt8aEpD9w7w/giphy.gif",
    ]
    return random.choice(angela_gifs)


def birthday_message():
    embed = nextcord.Embed(color=SUCCESS_COLOR, title='Happiest birthday from Angela Lansbury 9000!')
    embed.set_image(url=get_random_angela_gif())
    return embed


def get_birthday_number(year: int):
    current_year = nextcord.utils.utcnow().year
    birthday_number = current_year - year
    if birthday_number <= 0:
        return "0th"
    SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
    if 10 <= birthday_number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = SUFFIXES.get(birthday_number % 10, 'th')
    return str(birthday_number) + suffix


def birthday_entry(embed: nextcord.Embed, birthday: Birthday, member: nextcord.Member):
    embed.add_field(name='\u200b',
                    value=f'{member.mention} a very happy {get_birthday_number(birthday.year)} birthday to {birthday.name.title()}!',
                    inline=False)
    return embed


def get_special_birthday_fields(embed: nextcord.Embed):
    # if today is October 16th
    if nextcord.utils.utcnow().strftime('%m-%d') == '10-16':
        embed.add_field(name='\u200b',
                        value=f'And a very happy {get_birthday_number(1925)} birthday to dearest Dame Angela Brigid Lansbury, may she rest in peace!',
                        inline=False)
    # if today is March 1st and it's not a leap year
    if nextcord.utils.utcnow().strftime('%m-%d') == '03-01' and not nextcord.utils.utcnow().year % 4 == 0:
        embed.add_field(name='\u200b', value=f'And a very happy birthday to those celebrating a leap year birthday.',
                        inline=False)
    return embed
