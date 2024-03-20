import nextcord
import sentry_sdk

from bot.cogs.polls.views.poll_view import PollView
from db import PollQuestion, DB
from db.helpers import polls_helper


class FinalizePollView(nextcord.ui.View):
    def __init__(self, poll_question: PollQuestion):
        super().__init__()
        self.poll_question = poll_question
        self.toggle_anonymous.emoji = '✅' if self.poll_question.is_anonymous else '❌'
        self.toggle_multiselect.emoji = '✅' if self.poll_question.is_multi_choice else '❌'

    @nextcord.ui.button(label='Send Poll', style=nextcord.ButtonStyle.primary)
    async def send_poll(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            polls_helper.save(self.poll_question)
            poll_view = PollView(self.poll_question)
            message = await interaction.channel.send(poll_view.content, embed=poll_view.results_embed, view=poll_view)
            self.poll_question.message_id = message.id
            polls_helper.save(self.poll_question)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.response.edit_message(content='Something went wrong. Try again.', view=None)
            raise
        await interaction.response.edit_message(content='Poll sent!', view=None)
        self.stop()

    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.danger)
    async def cancel(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(content='Canceled.', view=None)
        self.stop()

    @nextcord.ui.button(label='Toggle Anonymous', style=nextcord.ButtonStyle.secondary)
    async def toggle_anonymous(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.poll_question.is_anonymous = not self.poll_question.is_anonymous
        self.toggle_anonymous.emoji = '✅' if self.poll_question.is_anonymous else '❌'
        await interaction.response.edit_message(view=self)

    @nextcord.ui.button(label='Toggle Multiselect', style=nextcord.ButtonStyle.secondary)
    async def toggle_multiselect(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.poll_question.is_multi_choice = not self.poll_question.is_multi_choice
        self.toggle_multiselect.emoji = '✅' if self.poll_question.is_multi_choice else '❌'
        await interaction.response.edit_message(view=self)
