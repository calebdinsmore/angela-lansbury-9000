from typing import List

import nextcord
import sentry_sdk
import sqlalchemy as sa
from nextcord import slash_command, Interaction, SlashOption, Permissions
from nextcord.ext import commands

from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, ANGELA_TECH_SUPPORT_ID, BUMPERS_GUILD_ID
from db import ImageMessageToDelete, DB


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='send-message',
                   description='Send a message to a channel.',
                   guild_ids=[TESTING_GUILD_ID, BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def send_message(self,
                           interaction: Interaction,
                           message: str = SlashOption(name='message',
                                                      description='Message to send'),
                           reply_to: str = SlashOption(name='reply_to',
                                                       description='Message ID to reply to',
                                                       required=False)):
        await interaction.response.defer(ephemeral=True)
        try:
            if reply_to:
                reply_to_message = await interaction.channel.fetch_message(int(reply_to))
                await reply_to_message.reply(message)
            else:
                await interaction.channel.send(message)
            await interaction.send('Sent!', ephemeral=True)
        except Exception as e:
            await interaction.send(f'Something went wrong: {e}', ephemeral=True)

    @slash_command(name='summary',
                   description='Summary of guilds Angela has been added to.',
                   guild_ids=[TESTING_GUILD_ID])
    async def summary(self, interaction: Interaction, name: str = SlashOption(name='name', required=False)):
        guilds = '\n'.join([f'- {g.name} {g.id if name is not None and name.lower() in g.name.lower() else ""}'
                            for g in self.bot.guilds])
        embed = nextcord.Embed(description=guilds)
        embed.add_field(name='Server Count', value=len(self.bot.guilds))
        await interaction.send(embed=embed)

    @slash_command(name='owner-blast', description='Send a message to all server owners using Angela who arent in'
                                                   ' the tech support server.',
                   guild_ids=[TESTING_GUILD_ID])
    async def owner_blast(self,
                          interaction: Interaction,
                          confirmation: str = SlashOption(name='confirmation',
                                                          choices=['Test', 'Send']),
                          message: str = SlashOption(name='message')):
        await interaction.response.defer()
        owners_to_send_to = []
        tech_support_guild_members = self.bot.get_guild(ANGELA_TECH_SUPPORT_ID).members
        for guild in self.bot.guilds:
            if guild.owner not in tech_support_guild_members:
                owners_to_send_to.append(guild.owner)

        if confirmation == 'Test':
            channel = self.bot.get_channel(interaction.channel_id)
            await interaction.send('Sending message as test.')
            await channel.send(message, suppress_embeds=True)
            await channel.send(f'Would have sent to the following owners: {[ o.name for o in owners_to_send_to ]}')
            return

        failures = []
        owner_name = None
        sent_to = set()
        try:
            for owner in owners_to_send_to:
                if owner.id in sent_to:
                    continue
                owner_name = owner.name
                await owner.send(message, suppress_embeds=True)
                sent_to.add(owner.id)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            failures.append(owner_name)

        await interaction.send('Sent mass message.', embed=messages.error(f'Failures: {failures}'))

    @slash_command(name='list-non-ratifiers',
                   guild_ids=[BUMPERS_GUILD_ID],
                   default_member_permissions=Permissions(manage_guild=True))
    async def list_non_ratifiers(self, interaction: Interaction):
        message_id = 1212871675440537630
        guild = self.bot.get_guild(BUMPERS_GUILD_ID)
        channel = await self.bot.fetch_channel(1212784801388429394)
        message = await channel.fetch_message(message_id)
        ayes = await message.reactions[0].users().flatten()
        aye_member_ids = [a.id for a in ayes]
        non_voters = [m for m in guild.members if m.id not in aye_member_ids and not m.bot]
        non_voters_string = '\n'.join([f'- {nv.mention}' for nv in non_voters])
        content = '## Non-Ratifiers\n\n' + non_voters_string
        await interaction.send(content, ephemeral=True)

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
