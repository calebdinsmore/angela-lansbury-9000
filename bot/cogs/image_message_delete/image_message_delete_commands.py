"""
ImageMessageDeleteCommands

This cog doesn't have any commands (yet), but it does hold the looping task that checks for any messages users
have marked for eventual deletion.
"""

import asyncio
import datetime as dt
from typing import List

import nextcord
import sentry_sdk
import sqlalchemy as sa
from nextcord import slash_command, Permissions, Interaction, SlashOption
from nextcord.ext import commands, tasks

from bot.utils import messages
from bot.utils.constants import BUMPERS_GUILD_ID, TESTING_GUILD_ID
from db import DB, ImageMessageToDelete


class ImageMessageDeleteCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_expired_messages.start()

    @tasks.loop(hours=1)
    async def check_for_expired_messages(self):
        if not self.bot.is_ready():
            return
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        expired_messages: List[ImageMessageToDelete] = DB.s.execute(
            sa.select(ImageMessageToDelete)
            .where(ImageMessageToDelete.delete_after < now)
            .where(ImageMessageToDelete.has_failed == None)
        ).scalars().all()
        for db_message_to_delete in expired_messages:
            guild = self.bot.get_guild(db_message_to_delete.guild_id)
            channel = guild.get_channel(db_message_to_delete.channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(db_message_to_delete.channel_id)
            try:
                message = await channel.fetch_message(db_message_to_delete.message_id)
                await message.delete()
                DB.s.delete(db_message_to_delete)
            except nextcord.NotFound:
                sentry_sdk.capture_message(f'Failed to find message {db_message_to_delete}')
                db_message_to_delete.has_failed = True
            except Exception as e:
                sentry_sdk.capture_exception(e)
                db_message_to_delete.has_failed = True
            finally:
                DB.s.commit()

    @check_for_expired_messages.error
    async def check_for_expired_messages_error(self, e):
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.check_for_expired_messages.restart()

    @slash_command(name='image-deleter', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def image_deleter(self, interaction: Interaction):
        pass

    @image_deleter.subcommand(name='retry', description='Retry failed image deletions.')
    async def retry(self, interaction: Interaction, delete_failures: bool = SlashOption(name='delete-failures')):
        await interaction.response.defer()
        retry_results: List[str] = []
        failed_messages: List[ImageMessageToDelete] = DB.s.execute(
            sa.select(ImageMessageToDelete)
            .where(ImageMessageToDelete.has_failed == True)
        ).scalars().all()
        deletions = 0
        failures = 0
        for failed_message in failed_messages:
            try:
                guild = self.bot.get_guild(failed_message.guild_id)
                channel = guild.get_channel(failed_message.channel_id)
                if not channel:
                    channel = await self.bot.fetch_channel(failed_message.channel_id)
                message = await channel.fetch_message(failed_message.message_id)
                await message.delete()
                retry_results.append(f'- Successfully deleted message {failed_message}. Deleting record.')
                deletions += 1
                DB.s.delete(failed_message)
            except Exception as e:
                retry_results.append(f'- Hit exception ({e}) for {failed_message}.')
                failures += 1
                if delete_failures:
                    DB.s.delete(failed_message)
        DB.s.commit()
        result_message = '\n'.join(retry_results)
        result_message += f'\nSuccessful deletions: {deletions}\n' \
                          f'Failed retries: {failures}'
        if len(retry_results) == 0:
            result_message = 'No failed deletions found.'
        await interaction.send(embed=messages.success(result_message), ephemeral=True)

