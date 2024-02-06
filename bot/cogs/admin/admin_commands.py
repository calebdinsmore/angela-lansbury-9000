from typing import List

import nextcord
import sentry_sdk
import sqlalchemy as sa
from nextcord import slash_command, Interaction, SlashOption, Permissions
from nextcord.ext import commands

from bot.events.handlers.temp_discussion_handler import REACTION_CHANNEL_ID, REACTION_MESSAGE_ID, ROLE_ID, \
    REACTION_EMOJI
from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, ANGELA_TECH_SUPPORT_ID, BUMPERS_GUILD_ID
from db import ImageMessageToDelete, DB


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='distribute-role',
                   description='Initialize discussion role distribution',
                   guild_ids=[BUMPERS_GUILD_ID])
    async def distribute_role(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            reaction_channel = await self.bot.fetch_channel(REACTION_CHANNEL_ID)
            reaction_message = await reaction_channel.fetch_message(REACTION_MESSAGE_ID)
            reactions = reaction_message.reactions
            added = 0
            for reaction in reactions:
                if str(reaction.emoji) != REACTION_EMOJI:
                    continue
                async for user in reaction.users():
                    if user.bot:
                        continue
                    member = interaction.guild.get_member(user.id)
                    if member is None:
                        continue
                    role = nextcord.utils.get(interaction.guild.roles, id=ROLE_ID)
                    if role is None:
                        continue
                    await member.add_roles(role)
                    added += 1
        except Exception as e:
            return await interaction.send(f'Something went wrong: {e}', ephemeral=True)
        await interaction.send(f'Added {added} roles.', ephemeral=True)

    @slash_command(name='summary',
                   description='Summary of guilds Angela has been added to.',
                   guild_ids=[TESTING_GUILD_ID])
    async def summary(self, interaction: Interaction):
        embed = nextcord.Embed()
        embed.add_field(name='Server Count', value=len(self.bot.guilds))
        guilds = '\n'.join([f'- {g.name}' for g in self.bot.guilds])
        embed.add_field(name='Servers', value=guilds, inline=False)
        await interaction.send(embed=embed)

    @slash_command(name='guild-owner', description='Find Guild Owner', guild_ids=[TESTING_GUILD_ID])
    async def guild_owner(self, interaction: Interaction, guild_name: str = SlashOption(name='guild-name')):
        for guild in self.bot.guilds:
            if guild.name.lower() == guild_name.lower():
                await interaction.send(f'Found guild owner: {guild.owner.name} | {guild.owner.display_name} | {guild.owner.mention}')
                return
        await interaction.send('Unable to find guild with that name.')

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
