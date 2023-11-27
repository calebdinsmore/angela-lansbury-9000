import nextcord
import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext import commands

from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID


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

    @slash_command(name='owner-blast', description='Send a message to all server owners using Angela.',
                   guild_ids=[TESTING_GUILD_ID])
    async def owner_blast(self,
                          interaction: Interaction,
                          confirmation: str = SlashOption(name='confirmation',
                                                          choices=['Test', 'Send']),
                          message: str = SlashOption(name='message')):
        await interaction.response.defer()
        if confirmation == 'Test':
            channel = self.bot.get_channel(interaction.channel_id)
            await interaction.send('Sending message as test.')
            await channel.send(message)
            return

        failures = []
        owner_name = None
        sent_to = set()
        try:
            for guild in self.bot.guilds:
                if guild.owner_id in sent_to:
                    continue
                owner_name = guild.owner.name
                await guild.owner.send(message)
                sent_to.add(guild.owner_id)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            failures.append(owner_name)

        await interaction.send('Sent mass message.', embed=messages.error(f'Failures: {failures}'))
