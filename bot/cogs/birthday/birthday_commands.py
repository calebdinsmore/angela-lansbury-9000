from nextcord import slash_command, Interaction, SlashOption, Permissions, Member
from nextcord.ext import commands

from bot.config import Config
from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID


class BirthdayCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='birthday', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   description='Birthday commands')
    async def birthday(self, interaction: Interaction):
        print('birthday')
        pass

    @birthday.subcommand(name='add', description='Add a birthday')
    async def birthday_add(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                         description='User to add birthday for.'),
                            name: str = SlashOption(name='name', description='Name of person celebrating a birthday'),
                            date: str = SlashOption(name='date', description='Date of birthday (MM/DD/YYYY)')):
        if interaction.guild is not None and interaction.guild_id not in [BUMPERS_GUILD_ID, TESTING_GUILD_ID]:
            return await interaction.send(embed=messages.error('Birthday tracking is unsupported in this server.'))
        print(user, name, date)
        await interaction.send('Not implemented yet.')

    @birthday.subcommand(name='list', description='List birthdays')
    async def birthday_list(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                         description='User to list birthdays for.'),):
        if interaction.guild is not None and interaction.guild_id not in [BUMPERS_GUILD_ID, TESTING_GUILD_ID]:
            return await interaction.send(embed=messages.error('Birthday tracking is unsupported in this server.'))
        print('list')
        await interaction.send('Not implemented yet.')

    @birthday.subcommand(name='remove', description='Remove a birthday')
    async def birthday_remove(self, interaction: Interaction,
                                user: Member = SlashOption(name='user',
                                                                description='User to remove birthday for.'),
                                number: int = SlashOption(name='number', description='Number of birthday to remove')):
        if interaction.guild is not None and interaction.guild_id not in [BUMPERS_GUILD_ID, TESTING_GUILD_ID]:
            return await interaction.send(embed=messages.error('Birthday tracking is unsupported in this server.'))
        print(user)
        await interaction.send('Not implemented yet.')
