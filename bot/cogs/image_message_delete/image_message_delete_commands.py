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
from nextcord import slash_command, Permissions, Interaction, SlashOption, TextChannel
from nextcord.ext import commands, tasks

from bot.utils import messages
from bot.utils.constants import BUMPERS_GUILD_ID, TESTING_GUILD_ID
from db import DB, ImageMessageToDelete
from db.helpers import image_message_helper, user_settings_helper


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
            try:
                channel = guild.get_channel(db_message_to_delete.channel_id)
                if not channel:
                    channel = await self.bot.fetch_channel(db_message_to_delete.channel_id)
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

    @slash_command(name='image-deletion-admin', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def image_deleter(self, interaction: Interaction):
        pass

    @image_deleter.subcommand(name='retry', description='Retry failed image deletions.')
    async def retry(self, interaction: Interaction, delete_failures: bool = SlashOption(name='delete-failures')):
        await interaction.response.defer(ephemeral=True)
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

    @slash_command(name='my-image-deletion', force_global=True)
    async def image_deleter_settings(self, interaction: Interaction):
        pass

    @image_deleter_settings.subcommand(name='show-settings', description='Show your image deletion settings.')
    async def show_settings(self, interaction: Interaction):
        user_settings = user_settings_helper.get_user_settings(interaction.user.id, interaction.guild_id)
        all_channel_settings = image_message_helper.get_all(interaction.guild_id, interaction.user.id)
        embed = nextcord.Embed()
        embed.add_field(name='Enabled?', value='✅' if user_settings.image_deletion_prompts_enabled else '❌')
        channel_setting_strings = []
        for channel_setting in all_channel_settings:
            channel = interaction.guild.get_channel(channel_setting.channel_id)
            setting_text = 'Keep'
            if channel_setting.delete_after > 0:
                setting_text = f'{channel_setting.delete_after} days'
            channel_setting_strings.append(f'{channel.mention}: {setting_text}')
        embed.add_field(name='Channel Settings', value='\n'.join(channel_setting_strings), inline=False)

        content = None if user_settings.image_deletion_prompts_enabled else 'Note: channel-specific settings are ' \
                                                                            'irrelevant because image deletion ' \
                                                                            'is disabled.'
        await interaction.send(content, embed=embed, ephemeral=True)

    @image_deleter_settings.subcommand(name='set-enabled',
                                       description='Enable/disable image deletion prompts for your images.')
    async def set_enabled(self, interaction: Interaction, enabled: str = SlashOption(name='enabled',
                                                                                     choices=['✅', '❌'])):
        is_enabled = enabled == '✅'
        user_settings_helper.set_image_deletion_enabled(interaction.user.id, interaction.guild_id, is_enabled)
        confirmation_word = 'Enabled' if is_enabled else 'Disabled'
        note = '' if is_enabled else '\nAny images currently marked for deletion will still be deleted as scheduled.'
        await interaction.send(embed=messages.success(f'{confirmation_word} image prompts in this server.{note}'),
                               ephemeral=True)

    @image_deleter_settings.subcommand(name='channel-default',
                                       description='Change your settings for image deletion in a channel.')
    async def channel_default(self,
                              interaction: Interaction,
                              channel: TextChannel = SlashOption(name='channel',
                                                                 description='Channel to set settings for.'),
                              delete_after: str = SlashOption(name='delete-after',
                                                              description='How long to wait before deleting the message.',
                                                              choices=['1d', '7d', '14d', '30d', 'keep'])):
        image_deletion_days = {
            '1d': 1,
            '7d': 7,
            '14d': 14,
            '30d': 30,
            'keep': 0
        }
        image_message_helper.change_user_channel_delete_settings(interaction.guild.id, channel.id, interaction.user.id,
                                                                 image_deletion_days[delete_after])
        await interaction.send(
            f"Setting your image deletion settings for channel {channel.mention} to **{delete_after}**",
            ephemeral=True)

    @image_deleter_settings.subcommand(name='reset-channel',
                                       description='Remove your settings for image deletion in a channel.')
    async def reset(self, interaction: Interaction, channel: TextChannel = SlashOption(name='channel',
                                                                                       description='Channel to remove settings for.')):
        image_message_helper.reset_user_channel_delete_settings(interaction.guild.id, channel.id, interaction.user.id)
        await interaction.send(f"Removing image deletion settings for channel {channel.mention}.", ephemeral=True)
