from datetime import datetime, timezone, time
import asyncio
import calendar
from typing import List

import nextcord
import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption, Member, TextChannel, Permissions
from nextcord.ext import commands, tasks

from bot.utils import messages
from db.helpers import birthday_helper


async def fetch_member_map(guild: nextcord.Guild, user_ids: List[int]):
    user_ids = list(set(user_ids))
    birthday_members = await guild.query_members(user_ids=user_ids)
    member_map = {m.id: m for m in birthday_members}
    return member_map


class BirthdayCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.post_birthdays.start()

    # Every day at 5AM Pacific Time
    @tasks.loop(time=time(hour=12, minute=0, second=0, tzinfo=timezone.utc))
    async def post_birthdays(self):
        if not self.bot.is_ready():
            return

        birthdays_by_guild_id = birthday_helper.get_todays_birthdays()
        for guild_id, birthdays in birthdays_by_guild_id.items():
            try:
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    # Can't find guild, skip posting these birthdays
                    continue
                user_ids = [b.user_id for b in birthdays]
                member_map = await fetch_member_map(guild, user_ids)
                birthday_channel_id = birthday_helper.get_birthday_channel_id(guild_id)
                if birthday_channel_id is None:
                    # No birthday channel set, skip posting these birthdays
                    continue
                channel = self.bot.get_channel(birthday_channel_id)
                if channel is None:
                    # Can't find channel, skip posting these birthdays
                    continue
                # Assemble birthday message
                message = messages.birthday_message()
                for birthday in birthdays:
                    member = member_map.get(birthday.user_id)
                    if member is None:
                        # Can't find member, skip this birthday
                        continue
                    message = messages.birthday_entry(message, birthday, member)
                message = messages.get_special_birthday_fields(message)
                if len(message.fields) == 0:
                    # No birthdays to post, skip posting
                    continue
                await channel.send(embed=message)
            except nextcord.Forbidden as e:
                sentry_sdk.capture_message(f'Lacked permissions to send birthday messages for {guild.name}. Notify '
                                           f'{guild.owner.name} about permissions issue.')
                sentry_sdk.capture_exception(e)
            except Exception as e:
                sentry_sdk.capture_message(f'Unable to send birthday messages for {guild.name}')
                sentry_sdk.capture_exception(e)
        baby_month_milestones = birthday_helper.get_todays_baby_month_milestones()
        for guild_id, birthdays in baby_month_milestones.items():
            try:
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    # Can't find guild, skip posting these birthdays
                    continue
                user_ids = [b.user_id for b in birthdays]
                member_map = await fetch_member_map(guild, user_ids)
                baby_month_milestone_channel_id = birthday_helper.get_baby_month_milestone_channel_id(guild_id)
                if baby_month_milestone_channel_id is None:
                    # No baby month milestone channel set, skip posting these birthdays
                    continue
                channel = self.bot.get_channel(baby_month_milestone_channel_id)
                if channel is None:
                    # Can't find channel, skip posting these birthdays
                    continue
                # Assemble baby month milestone message
                for birthday in birthdays:
                    member = member_map.get(birthday.user_id)
                    if member is None:
                        # Can't find member, skip this message
                        continue
                    message = messages.baby_month_milestone_message(birthday, member)
                    await channel.send(embed=message)
            except nextcord.Forbidden as e:
                sentry_sdk.capture_message(f'Lacked permissions to send milestone messages for {guild.name}. Notify '
                                           f'{guild.owner.name} about permissions issue.')
                sentry_sdk.capture_exception(e)
            except Exception as e:
                sentry_sdk.capture_message(f'Unable to send baby month milestone messages for {guild.name}')
                sentry_sdk.capture_exception(e)

    @post_birthdays.error
    async def post_birthdays_error(self, e):
        print(e)
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.post_birthdays.restart()

    ##############################
    # Admin Slash Commands
    ##############################

    @slash_command(name='birthday-admin',
                   description='Birthday commands for admins',
                   default_member_permissions=Permissions(manage_guild=True))
    async def birthday_admin(self, interaction: Interaction):
        pass

    @birthday_admin.subcommand(name='config', description='Configure birthday settings')
    async def birthday_config(self, interaction: Interaction,
                              birthday_channel: TextChannel = SlashOption(name='birthday_channel',
                                                                          description='Channel to post birthday messages in.',
                                                                          required=False),
                              baby_month_milestone_channel: TextChannel = SlashOption(
                                  name='baby_month_milestone_channel',
                                  description='Channel to post baby month milestone messages in.', required=False)):
        if birthday_channel is not None:
            success = birthday_helper.update_birthday_channel_settings(interaction.guild_id, birthday_channel.id)
            if not success:
                return await interaction.send(f'An error occurred when updating birthday channel settings.',
                                              ephemeral=True)

        if baby_month_milestone_channel is not None:
            success = birthday_helper.update_baby_month_channel_settings(interaction.guild_id,
                                                                         baby_month_milestone_channel.id)
            if not success:
                return await interaction.send(f'An error occurred when updating baby milestone channel settings.',
                                              ephemeral=True)
        await interaction.send('Successfully updated birthday settings!', ephemeral=True)

    @birthday_admin.subcommand(name='add', description='Add a birthday')
    async def birthday_admin_add(self, interaction: Interaction,
                                 user: Member = SlashOption(name='user', description='User to add birthday for'),
                                 name: str = SlashOption(name='name',
                                                         description='Name of person celebrating a birthday'),
                                 date: str = SlashOption(name='date', description='Date of birthday (YYYY/MM/DD)')):
        # Get date from added date, validate, and add to the database. Return an error if the name already exists or
        # the date is invalid.
        try:
            dt = datetime.strptime(date, '%Y/%m/%d')
            success = birthday_helper.add_birthday(interaction.guild_id, user.id, name.lower(), dt.month, dt.day,
                                                   dt.year)
            if success:
                await interaction.send(f'Birthday added: `{name} | {dt.strftime("%b %d, %Y")}`', ephemeral=True)
            else:
                await interaction.send(
                    f'Birthday already exists for {name.title()}. Try a different name, or remove the existing birthday first.',
                    ephemeral=True)
        except ValueError:
            return await interaction.send('Please provide a date in the format YYYY/MM/DD', ephemeral=True)

    @birthday_admin.subcommand(name='remove', description='Remove a birthday')
    async def birthday_admin_remove(self, interaction: Interaction,
                                    user: Member = SlashOption(name='user', description='User to remove birthday for'),
                                    name: str = SlashOption(name='name', description='Name of birthday to remove')):
        success = birthday_helper.delete_birthday(interaction.guild_id, user.id, name.lower())
        if not success:
            return await interaction.send(
                f'An error occurred when deleting birthday {name.title()} associated with user {user.display_name}.',
                ephemeral=True)
        await interaction.send(f'Successfully deleted birthday for {user.display_name}!', ephemeral=True)

    ##############################
    # Regular Slash Commands
    ##############################

    @slash_command(name='birthday',
                   description='Birthday commands',
                   force_global=True)
    async def birthday(self, interaction: Interaction):
        pass

    @birthday.subcommand(name='add', description='Add a birthday')
    async def birthday_add(self, interaction: Interaction,
                           name: str = SlashOption(name='name', description='Name of person celebrating a birthday'),
                           date: str = SlashOption(name='date', description='Date of birthday (YYYY/MM/DD)')):
        # Get date from added date, validate, and add to the database. Return an error if the name already exists or the
        # date is invalid.
        try:
            dt = datetime.strptime(date, '%Y/%m/%d')
            success = birthday_helper.add_birthday(interaction.guild_id, interaction.user.id, name.lower(), dt.month,
                                                   dt.day, dt.year)
            if success:
                await interaction.send(f'Birthday added: `{name} | {dt.strftime("%b %d, %Y")}`', ephemeral=True)
            else:
                await interaction.send(f'Birthday already exists for {name.title()}. '
                                       f'Try a different name, or remove the existing birthday first.',
                                       ephemeral=True)
        except ValueError:
            return await interaction.send('Please provide a date in the format YYYY/MM/DD', ephemeral=True)

    @birthday.subcommand(name='list', description='List birthdays')
    async def birthday_list(self, interaction: Interaction,
                            user: Member = SlashOption(name='user',
                                                       description='User to list birthdays for.'), ):
        birthdays = birthday_helper.list_birthdays(interaction.guild_id, user.id)
        if len(birthdays) == 0:
            embed = messages.info(f'No stored birthdays found for {user.name}. Use `/birthday add` to add a birthday.')
            icon_url = user.avatar.url if user.avatar else None
            embed.set_author(name=user.name, icon_url=icon_url)
            return await interaction.send(embed=embed, ephemeral=True)
        embed = messages.info(
            f'Current birthdays stored for {user.name}. Use `/birthday remove` to remove a stored birthday.')
        icon_url = user.avatar.url if user.avatar else None
        embed.set_author(name=user.name, icon_url=icon_url)
        for birthday in birthdays:
            embed.add_field(name=birthday[0].name.title(),
                            value=f'{birthday[0].year}/{birthday[0].month}/{birthday[0].day}')
        await interaction.send(embed=embed, ephemeral=True)

    @birthday.subcommand(name='remove', description='Remove a birthday')
    async def birthday_remove(self, interaction: Interaction,
                              name: str = SlashOption(name='name', description='Name of birthday to remove')):
        success = birthday_helper.delete_birthday(interaction.guild_id, interaction.user.id, name.lower())
        if not success:
            return await interaction.send(f'An error occurred when deleting birthday {name.title()} '
                                          f'associated with user {interaction.user.display_name}.', ephemeral=True)
        await interaction.send('Successfully deleted birthday!', ephemeral=True)

    @birthday.subcommand(name='upcoming', description='Show birthdays in the next month')
    async def birthday_upcoming(self, interaction: Interaction):
        birthdays = birthday_helper.get_upcoming_birthdays(interaction.guild_id)
        if not birthdays:
            return await interaction.send('There are no birthdays in the next month', ephemeral=True)
        # Max of 25 embeds per message
        max_birthdays_per_chunk = 25
        birthday_chunks = [birthdays[i * max_birthdays_per_chunk:(i + 1) * max_birthdays_per_chunk] for i in
                           range((len(birthdays) + max_birthdays_per_chunk - 1) // max_birthdays_per_chunk)]
        guild = self.bot.get_guild(interaction.guild_id)
        user_ids = [b.user_id for b in birthdays]
        member_map = await fetch_member_map(guild, user_ids)
        for chunk in birthday_chunks:
            embed = messages.info(f'Upcoming birthdays in the next month:')
            for birthday in chunk:
                member = member_map.get(birthday.user_id)
                if member is None:
                    # Can't find member, skip this message
                    continue
                embed.add_field(name=f'{calendar.month_name[birthday.month]} {birthday.day}',
                                value=f'{member.mention}: {birthday.name.title()}', inline=False)
            await interaction.send(embed=embed, ephemeral=True)
