"""
AutoDeleteCommands
/auto-delete config
/auto-delete stop

This cog holds the task coroutine responsible for identifying and deleting stale messages as well as the slash
commands listed above that configure channels to get messages auto-deleted.
"""
import asyncio
from typing import List

import nextcord
import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption, Permissions
from nextcord.ext import commands, tasks

from bot.cogs.auto_delete import auto_delete_helper
from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID
from db import AutoDeleteType, DB, AutoDeleteChannelConfig


class AutoDeleteCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.check_for_stale_messages.start()
        self.bot = bot

    @tasks.loop(seconds=30)
    async def check_for_stale_messages(self):
        """
        This is the loop handler that periodically (every 30s) checks if any configured channels have stale messages
        that need to be pruned.
        """
        if not self.bot.is_ready():
            return
        configs: List[AutoDeleteChannelConfig] = DB.s.all(AutoDeleteChannelConfig)
        for config in configs:
            guild = self.bot.get_guild(config.guild_id)
            channel: nextcord.TextChannel = guild.get_channel(config.channel_id)
            try:
                anchor_message = await auto_delete_helper.fetch_anchor_message(channel, config)
            except nextcord.NotFound:
                await channel.send(embed=messages.error('Failed to find anchor message for auto delete. '
                                                        'Please reconfigure auto-delete in this channel.'))
                auto_delete_helper.remove_channel_config(config.guild_id, config.channel_id)
                continue
            all_messages = await channel.history(after=anchor_message).flatten()
            stale_messages = auto_delete_helper.get_stale_messages(all_messages, config)
            for m in stale_messages:
                await m.delete()

    @check_for_stale_messages.error
    async def check_for_stale_messages_error(self, e):
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.check_for_stale_messages.restart()

    @slash_command(name='auto-delete', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def auto_delete(self, interaction: Interaction):
        """
        This is the command prefix for the following sub-commands enumerated below.
        """
        pass

    @auto_delete.subcommand(description='Configure auto-delete settings for the current channel')
    async def config(self,
                     interaction: Interaction,
                     delete: str = SlashOption(description='Types of messages to delete',
                                               choices=AutoDeleteType.list()),
                     delete_after: int = SlashOption(description='Delay before deleting messages, in MINUTES')):
        await interaction.send(embed=messages.success(f'{delete.title()} messages in this channel '
                                                      f'posted after this message will be deleted '
                                                      f'after {delete_after} minutes.\n\n'
                                                      f"(**Don't** delete this message. This bot uses "
                                                      f"it to anchor searches against this channel's history.)"))
        message = await interaction.original_message()
        current_config: AutoDeleteChannelConfig = DB.s.first(AutoDeleteChannelConfig,
                                                             guild_id=interaction.guild_id,
                                                             channel_id=interaction.channel_id)
        if current_config is None:
            current_config = AutoDeleteChannelConfig(guild_id=interaction.guild_id,
                                                     channel_id=interaction.channel_id,
                                                     auto_delete_type=delete,
                                                     delete_after_minutes=delete_after,
                                                     anchor_message=message.id,
                                                     original_anchor_message=message.id)
            DB.s.add(current_config)
        else:
            current_config.auto_delete_type = delete
            current_config.delete_after_minutes = delete_after
            current_config.anchor_message = message.id
            current_config.original_anchor_message = message.id
        DB.s.commit()

    @auto_delete.subcommand(description='Stop auto-deletion in this channel.')
    async def stop(self, interaction: Interaction):
        try:
            auto_delete_helper.remove_channel_config(interaction.guild_id, interaction.channel_id)
        except auto_delete_helper.ConfigNotFound:
            return await interaction.send(
                embed=messages.error("This channel isn't configured to auto-delete messages."))
        await interaction.send(embed=messages.success('Stopped auto-deletions in this channel.'))
