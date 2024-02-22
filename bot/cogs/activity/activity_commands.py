import asyncio

import nextcord
import sentry_sdk
from nextcord import Permissions, slash_command, Interaction, SlashOption
from nextcord.ext import commands, tasks

from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID
from bot.utils.logger import get_logger, LoggingLevel
from db import DB, UserActivity
from db.helpers import activity_module_settings_helper, user_activity_helper, rolling_message_log_helper


class ActivityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_inactives.start()

    @tasks.loop(hours=24)
    async def check_for_inactives(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        inactives = rolling_message_log_helper.get_inactive_users()
        for user_id, guild_id in inactives:
            logger = get_logger(LoggingLevel.ACTIVITY, guild_id)
            settings = activity_module_settings_helper.get_settings(guild_id)
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(user_id)
            user_activity: UserActivity = DB.s.first(UserActivity, user_id=user_id, guild_id=guild_id)
            if user_activity is None:
                user_activity_helper.setup_user(user_id, guild_id)
                continue
            if member is None:
                get_logger(LoggingLevel.GENERAL).log(f'{guild.name}: {user_id} left server. Marking inactive.')
                user_activity.is_active = False
                DB.s.commit()
                continue
            if nextcord.utils.get(member.roles, id=settings.model.break_role_id):
                if rolling_message_log_helper.user_in_sixty_day_inactives(user_id,guild_id) and not user_activity.sent_sixty_day_notice:
                    await logger.log(f'⚠️ {member.mention} has been inactive for at least 60 days.')
                    user_activity.sent_sixty_day_notice = True
                    DB.s.commit()
            elif not nextcord.utils.get(member.roles,
                                        id=settings.model.inactive_role_id) and not user_activity.sent_thirty_day_notice:
                await logger.log(f'⚠️ {member.mention} has been inactive for at least 30 days.')
                user_activity.sent_thirty_day_notice = True
                DB.s.commit()

    @check_for_inactives.error
    async def check_for_inactives_error(self, e):
        sentry_sdk.capture_exception(e)
        await asyncio.sleep(60)
        self.check_for_inactives.restart()

    @slash_command(name='activity', guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def activity(self, interaction: Interaction):
        pass

    @activity.subcommand(name='stats', description='View your activity stats.')
    async def stats(self, interaction: Interaction):
        messages_last_thirty = rolling_message_log_helper.message_count_for_author(interaction.user.id,
                                                                                   interaction.guild_id,
                                                                                   30)
        messages_last_ninety = rolling_message_log_helper.message_count_for_author(interaction.user.id,
                                                                                   interaction.guild_id,
                                                                                   90)
        messages_last_ninety = round(messages_last_ninety / 3, 2)
        embed = messages.info('Here are your activity stats.')
        embed.add_field(name='Messages sent in the last 30 days', value=messages_last_thirty)
        embed.add_field(name='Rolling monthly average (last 90 days)', value=messages_last_ninety)
        await interaction.send(embed=embed, ephemeral=True)

    @activity.subcommand(name='initialize', description='Initialize user activity db')
    async def initialize(self, interaction: Interaction):
        await interaction.response.defer(with_message=True)
        user_activity_helper.initialize_user_activity(interaction.guild.members, interaction.guild_id)
        await interaction.send('DB initialized.')

    @activity.subcommand(name='show-settings', description='Show the current activity settings.')
    async def show_settings(self, interaction: Interaction):
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        inactive_role = None
        excluded_channels = None
        break_role = None
        if settings.model.inactive_role_id:
            inactive_role = interaction.guild.get_role(settings.model.inactive_role_id)
        if settings.model.excluded_channels:
            excluded_channels = [self._get_channel_if_exists(c_id) for c_id in settings.excluded_channels]
        if settings.model.break_role_id:
            break_role = interaction.guild.get_role(settings.model.break_role_id)
        message = messages.info('Here are your current activity settings:')
        message.add_field(name='Inactive Role', value=inactive_role.mention if inactive_role else 'Not Set')
        message.add_field(name='Break Role', value=break_role.mention if break_role else 'Not Set')
        message.add_field(name='Excluded Channels',
                          value='\n'.join([c for c in excluded_channels]) if excluded_channels else 'None')
        await interaction.send(embed=message, ephemeral=True)

    @activity.subcommand(name='exclude-channel', description='Exclude a channel from counting toward activity')
    async def exclude_channel(self,
                              interaction: Interaction,
                              channel: nextcord.TextChannel = SlashOption(name='channel')):
        settings = activity_module_settings_helper.get_settings(interaction.guild_id)
        settings.add_excluded_channel(channel.id)
        message = f'Excluded {channel.mention} from counting toward server activity.'
        if not self._can_see_channel(channel.id):
            message += "\n\n⚠️ It looks like I'm unable to see that channel, so it would have been excluded anyway. " \
                       "Ensure that I'm present in all channels you wish to track activity within."
        await interaction.send(message)

    @activity.subcommand(name='set-log-channel', description='Set the channel to log activity notifications to')
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

    @activity.subcommand(name='reactivate-member', description='Reactivate a server member')
    async def reactivate_member(self,
                                interaction: Interaction,
                                member: nextcord.Member = SlashOption(name='member')):
        user_activity_helper.setup_user(member.id, interaction.guild_id)
        await interaction.send(f'Reactivated {member.name}.')

    @activity.subcommand(name='set-inactive-role', description='Configure the inactive role')
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

    @activity.subcommand(name='set-break-role', description='Configure the "on break" role')
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
