import asyncio

import nextcord
import sentry_sdk
from nextcord import Permissions, slash_command, Interaction, SlashOption
from nextcord.ext import commands, tasks

from bot.cogs.activity import activity_manager
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID
from bot.utils.logger import get_logger, LoggingLevel
from db import DB, UserActivity
from db.helpers import activity_module_settings_helper, user_activity_helper, rolling_message_log_helper


class ActivityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.process_activity_roles.start()

    @tasks.loop(hours=12)
    async def process_activity_roles(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        try:
            await activity_manager.process_activity_roles_task(self.bot)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    """
    Activity Commands
    """
    @slash_command(name='activity', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID])
    async def activity(self, interaction: Interaction):
        pass

    @activity.subcommand(name='stats', description='View your activity stats.')
    async def stats(self, interaction: Interaction):
        await activity_manager.show_stats(interaction)

    """
    Activity Admin Commands
    """
    @slash_command(name='activity-admin', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def activity_admin(self, interaction: Interaction):
        pass

    @activity_admin.subcommand(name='add-activity-role', description='Set the role to be given to active members.')
    async def add_activity_role(self,
                                interaction: Interaction,
                                role: nextcord.Role = SlashOption(name='role'),
                                min_messages: int = SlashOption(name='min_messages',
                                                                description='Minimum messages to qualify for role',
                                                                required=False),
                                max_messages: int = SlashOption(name='max_messages',
                                                                description='Maximum messages to qualify for role',
                                                                required=False),
                                should_notify: bool = SlashOption(name='should_notify',
                                                                  description='Whether to notify the log channel when a'
                                                                              ' user is added to or removed from this '
                                                                              'role.',
                                                                  required=False),
                                rolling_month_window: int = SlashOption(name='rolling_month_window',
                                                                        description='How many prior months to average '
                                                                                    'for activity.',
                                                                        required=False)):
        await activity_manager.add_activity_role(interaction,
                                                 role,
                                                 min_messages,
                                                 max_messages,
                                                 should_notify,
                                                 rolling_month_window)

    @activity_admin.subcommand(name='remove-activity-role', description='Remove the role to be given to active members.')
    async def remove_activity_role(self, interaction: Interaction, role: nextcord.Role = SlashOption(name='role')):
        await activity_manager.remove_activity_role(interaction, role)

    @activity_admin.subcommand(name='server-stats', description='View the server\'s activity stats.')
    async def server_stats(self, interaction: Interaction):
        await activity_manager.show_server_stats(interaction)

    @activity_admin.subcommand(name='initialize', description='Initialize user activity db')
    async def initialize(self, interaction: Interaction):
        await interaction.response.defer(with_message=True)
        user_activity_helper.initialize_user_activity(interaction.guild.members, interaction.guild_id)
        await interaction.send('DB initialized.')

    @activity_admin.subcommand(name='show-settings', description='Show the current activity settings.')
    async def show_settings(self, interaction: Interaction):
        await activity_manager.show_settings(interaction, self.bot)

    @activity_admin.subcommand(name='toggle-channel-exclusion', description='Toggle whether a channel is excluded from '
                                                                      'activity tracking')
    async def exclude_channel(self,
                              interaction: Interaction,
                              channel: nextcord.TextChannel = SlashOption(name='channel')):
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        if channel.id in settings.excluded_channels:
            settings.remove_excluded_channel(channel.id)
            message = f'Included {channel.mention} in counting toward server activity.'
        else:
            settings.add_excluded_channel(channel.id)
            message = f'Excluded {channel.mention} from counting toward server activity.'
        if not self._can_see_channel(channel.id):
            message += "\n\n⚠️ It looks like I'm unable to see that channel, so it would have been excluded anyway. " \
                       "Ensure that I'm present in all channels you wish to track activity within."
        await interaction.send(message, ephemeral=True)

    @activity_admin.subcommand(name='set-log-channel', description='Set the channel to log activity notifications to')
    async def set_log_channel(self,
                              interaction: Interaction,
                              channel: nextcord.TextChannel = SlashOption(name='channel')):
        try:
            test_message = await channel.send('Testing')
            await test_message.delete()
        except (nextcord.NotFound, nextcord.Forbidden):
            await interaction.send(f"Looks like I'm not able to send messages in {channel.mention}. Make sure I have "
                                   f"access to that channel and try again.")
            return
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        settings.model.log_channel = channel.id
        DB.s.commit()
        await interaction.send(f'Set {channel} as the activity log channel.')

    @activity_admin.subcommand(name='reactivate-member', description='Reactivate a server member')
    async def reactivate_member(self,
                                interaction: Interaction,
                                member: nextcord.Member = SlashOption(name='member')):
        user_activity_helper.setup_user(member.id, interaction.guild_id)
        await interaction.send(f'Reactivated {member.name}.')

    @activity_admin.subcommand(name='set-inactive-role', description='Configure the inactive role')
    async def set_inactive(self,
                           interaction: Interaction,
                           role: nextcord.Role = SlashOption(name='role')):
        # can_manage_role = await self._can_manage_role(role)
        # if not can_manage_role:
        #     return await interaction.send(f"❌ It looks like I can't manage {role.name}. Make sure I have the `Manage "
        #                                   f"Roles` permission and that my role is higher than the chosen role in the "
        #                                   f"role hierarchy.")
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        settings.model.inactive_role_id = role.id
        DB.s.commit()
        await interaction.send(f'Set inactive role to `{role.name}`.')

    @activity_admin.subcommand(name='set-break-role', description='Configure the "on break" role')
    async def set_break(self,
                        interaction: Interaction,
                        role: nextcord.Role = SlashOption(name='role')):
        # can_manage_role = await self._can_manage_role(role)
        # if not can_manage_role:
        #     return await interaction.send(f"❌ It looks like I can't manage {role.name}. Make sure I have the `Manage "
        #                                   f"Roles` permission and that my role is higher than the chosen role in the "
        #                                   f"role hierarchy.")
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        settings.model.break_role_id = role.id
        DB.s.commit()
        await interaction.send(f'Set break role to `{role.name}`.')

    def _get_channel_if_exists(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return 'Channel Not Found'
        return channel.mention

    @staticmethod
    async def _can_manage_role(role: nextcord.Role):
        color = role.color
        try:
            await role.edit(color=65280, reason='Testing role permissions')
            await role.edit(color=color, reason='Restoring role color after test')
            return True
        except nextcord.Forbidden:
            return False

    def _can_see_channel(self, channel_id):
        if self.bot.get_channel(channel_id):
            return True
        else:
            return False
