from nextcord import slash_command, Interaction, SlashOption, Permissions
from nextcord.ext import commands

from bot.cogs.secret_santa import elf
from bot.cogs.secret_santa.elf import MemberMatchError
from bot.config import Config
from bot.utils import messages
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID


class SecretSantaCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='santa-admin', guild_ids=[TESTING_GUILD_ID])
    async def santa_admin(self, interaction: Interaction):
        pass

    @santa_admin.subcommand(name='clear', description='Clear pairings')
    async def santa_clear(self,
                          interaction: Interaction,
                          confirmation: str = SlashOption(name='confirmation',
                                                          description='type CONFIRM if you really intend to do this')):
        if confirmation != 'CONFIRM':
            return await interaction.send('Re-invoke with the "CONFIRM" argument to perform this command.')
        elf.clear_pairings()
        await interaction.send('Cleared pairings.')

    @santa_admin.subcommand(name='generate', description='Generate santa pairings')
    async def generate(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, with_message=True)
        try:
            if Config().is_prod:
                guild = self.bot.get_guild(BUMPERS_GUILD_ID)
            else:
                guild = interaction.guild
            models = elf.build_models_from_csv(guild)
            pairings = elf.generate_pairings(models)
            elf.persist_pairings(pairings)
            await interaction.send(embed=elf.pairings_embed(), ephemeral=True)
        except MemberMatchError as e:
            await interaction.send(f'Failed to find users for the following usernames:\n{e.failures}')
        except AssertionError as e:
            await interaction.send(f'Failed test: {e}. Try again.', ephemeral=True)
        except RuntimeError:
            await interaction.send('Pairing generation failed. Try again.', ephemeral=True)

    @santa_admin.subcommand(name='send-pairings', description='Send out pairings')
    async def send_pairings(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, with_message=True)
        if Config().is_prod:
            guild = self.bot.get_guild(BUMPERS_GUILD_ID)
        else:
            guild = interaction.guild
        failures = await elf.send_recipient_embeds(self.bot, guild)
        await interaction.send(f'Sent out recipient answers! Failures: {failures}')

    @santa_admin.subcommand(name='send-specific-pairing')
    async def send_specific_pairing(self, interaction: Interaction):
        guild = self.bot.get_guild(BUMPERS_GUILD_ID)
        await elf.send_recipient_embeds(self.bot, guild, specific_id=627666924087672833)
        await interaction.send(f'Pairing info sent to ID: 627666924087672833')

    @santa_admin.subcommand(name='remind', description='Remind Santas to send gifts')
    async def santa_remind(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, with_message=True)
        await elf.send_reminders(self.bot)
        await interaction.send('Reminders sent.')

    @slash_command(name='santa',
                   description='Secret santa commands',
                   dm_permission=True)
    async def santa(self, interaction: Interaction):
        pass

    @santa.subcommand(name='message', description='Send your gift recipient or Santa a message')
    async def santa_message(self, interaction: Interaction,
                            recipient: str = SlashOption(name='recipient',
                                                         description='Who to send this message to.',
                                                         choices=['Your Santa', 'Your Gift Recipient']),
                            message: str = SlashOption(name='message', description='The message you want to send.')):
        await elf.handle_santa_message(self.bot, interaction, recipient, message)

    @santa.subcommand(name='mark-sent', description='Mark your gift as sent')
    async def mark_sent(self, interaction: Interaction,
                        tracking_info: str = SlashOption(name='tracking-info',
                                                         description='Tracking info to give your '
                                                                     'recipient.')):
        ephemeral = interaction.guild is not None
        await elf.mark_sent(self.bot, interaction.user.id, tracking_info)
        await interaction.send('Your recipient has been notified. Thank you!', ephemeral=ephemeral)
