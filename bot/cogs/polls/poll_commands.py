import sentry_sdk
from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext import commands

from bot.cogs.polls.views.create_poll_modal import CreatePollModal
from bot.cogs.polls.views.poll_view import PollView
from bot.cogs.polls.views.util import update_poll_message
from bot.utils.constants import TESTING_GUILD_ID, BUMPERS_GUILD_ID
from db.helpers import polls_helper


class PollCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Register any open polls when the bot starts
        """
        try:
            open_polls = polls_helper.get_open_polls()
            for poll in open_polls:
                self.bot.add_view(PollView(poll))
        except Exception as e:
            sentry_sdk.capture_message('Failed to register open polls! Check log immediately.')
            sentry_sdk.capture_exception(e)

    @slash_command(name='poll', description='Poll commands', guild_ids=[BUMPERS_GUILD_ID, TESTING_GUILD_ID])
    async def poll(self, interaction: Interaction):
        pass

    @poll.subcommand(name='create', description='Create a poll')
    async def poll_create(self,
                          interaction: Interaction,
                          poll_question: str = SlashOption(name='question',
                                                           description='The question for the poll',
                                                           required=False)):
        await interaction.response.send_modal(CreatePollModal(poll_question))

    @poll.subcommand(name='close', description='Close a poll')
    async def poll_close(self, interaction: Interaction, poll_id: str = SlashOption(name='poll',
                                                                                      description='The poll to close')):
        await interaction.response.defer(with_message=True, ephemeral=True)
        poll = polls_helper.get_poll(int(poll_id))
        if poll:
            poll.is_open = False
            polls_helper.save(poll)
            await update_poll_message(poll.id, interaction.channel)
            await interaction.send('Poll closed!', ephemeral=True)

    @poll_close.on_autocomplete('poll_id')
    async def _on_poll_title_autocomplete(self, interaction: Interaction, focused_option: str):
        def shorten(text: str) -> str:
            return text[:50] + '...' if len(text) > 50 else text

        matching_polls = polls_helper.search_open_polls(focused_option)
        text_id_pairs = [(shorten(poll.text), str(poll.id)) for poll in matching_polls]
        text_id_pairs = dict(text_id_pairs)
        await interaction.response.send_autocomplete(text_id_pairs)

