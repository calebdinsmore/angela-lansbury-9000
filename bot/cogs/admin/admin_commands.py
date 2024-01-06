import nextcord
import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext import commands

from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, ANGELA_TECH_SUPPORT_ID


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='summary',
                   description='Summary of guilds Angela has been added to.',
                   guild_ids=[TESTING_GUILD_ID])
    async def summary(self, interaction: Interaction):
        embed = nextcord.Embed()
        embed.add_field(name='Server Count', value=len(self.bot.guilds))
        guilds = '\n'.join([f'- {g.name}' for g in self.bot.guilds])
        embed.add_field(name='Servers', value=guilds, inline=False)
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
            await channel.send(message)
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
