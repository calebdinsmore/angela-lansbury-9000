from datetime import datetime
import asyncio

from nextcord import slash_command, Interaction, SlashOption, Permissions, Member, TextChannel
from nextcord.ext import commands, tasks

from bot.config import Config
from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID
from db.helpers import birthday_helper


class BirthdayCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.post_birthdays.start()
    
    @tasks.loop(seconds=10)
    async def post_birthdays(self):
        if not self.bot.is_ready():
            return

        birthdays = birthday_helper.get_todays_birthdays()
        print("Todays birthdays:", birthdays)
        current_guild_id = None
        birthday_channel_id = None
        for birthday in birthdays:
            if birthday.guild_id != current_guild_id:
                current_guild_id = birthday.guild_id
                birthday_channel_id = birthday_helper.get_birthday_channel_id(current_guild_id)
                if birthday_channel_id is not None: 
                    channel = self.bot.get_channel(birthday_channel_id)
                    await channel.send(f'Todays birthdays: {birthday.name}')

    @post_birthdays.error
    async def post_birthdays_error(self, e):
        print('Error in post_birthdays')
        # sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.post_birthdays.restart()

    @slash_command(name='birthday', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   description='Birthday commands')
    async def birthday(self, interaction: Interaction):
        pass

    @birthday.subcommand(name='add', description='Add a birthday')
    async def birthday_add(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                         description='User to add birthday for.'),
                            name: str = SlashOption(name='name', description='Name of person celebrating a birthday'),
                            date: str = SlashOption(name='date', description='Date of birthday (MM/DD/YYYY)')):
        if interaction.guild is not None and interaction.guild_id not in [BUMPERS_GUILD_ID, TESTING_GUILD_ID]:
            return await interaction.send(embed=messages.error('Birthday tracking is unsupported in this server.'))
        # Get date from added date, validate, and add to the database. Return an error if the name already exists or the date is invalid.
        try:
            dt = datetime.strptime(date, '%m/%d/%Y')
            success = birthday_helper.add_birthday(interaction.guild_id, user.id, name.lower(), dt.month, dt.day, dt.year)
            if success:
                await interaction.send('Birthday added.')
            else:
                await interaction.send(f'Birthday already exists for {name.title()}. Try a different name, or remove the existing birthday first.')
        except ValueError:
            return await interaction.send('Please provide a date in the format MM/DD/YYYY')
        
    @birthday.subcommand(name='list', description='List birthdays')
    async def birthday_list(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                         description='User to list birthdays for.'),):
        birthdays = birthday_helper.list_birthdays(interaction.guild_id, user.id)
        if len(birthdays) == 0:
            embed = messages.info(f'No stored birthdays found for {user.name}. Use `/birthday add` to add a birthday.')
            icon_url = user.avatar.url if user.avatar else None
            embed.set_author(name=user.name, icon_url=icon_url)
            return await interaction.send(embed=embed)
        embed = messages.info(f'Current birthdays stored for {user.name}. Use `/birthday remove` to remove a stored birthday.')
        icon_url = user.avatar.url if user.avatar else None
        embed.set_author(name=user.name, icon_url=icon_url)
        for birthday in birthdays:
            embed.add_field(name=birthday[0].name.title(), value=f'{birthday[0].month}/{birthday[0].day}/{birthday[0].year}')
        await interaction.send(embed=embed)

    @birthday.subcommand(name='remove', description='Remove a birthday')
    async def birthday_remove(self, interaction: Interaction,
                                user: Member = SlashOption(name='user',
                                                                description='User to remove birthday for.'),
                                name: str = SlashOption(name='name', description='Name of birthday to remove')):
        success = birthday_helper.delete_birthday(interaction.guild_id, user.id, name.lower())
        if not success:
            return await interaction.send(f'An error occurred when deleting birthday {name.title()} associated with user {user.name}.')
        await interaction.send('Successfully deleted birthday!')

    @birthday.subcommand(name='config', description='Configure birthday settings')
    async def birthday_config(self, interaction: Interaction,
                                channel: TextChannel = SlashOption(name='channel',
                                                                description='Channel to post birthday messages in.')):
        success = birthday_helper.update_settings(interaction.guild_id, channel.id)
        if not success:
            return await interaction.send(f'An error occurred when updating birthday settings.')
        await interaction.send('Successfully updated birthday settings!')
