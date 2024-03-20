import nextcord
from nextcord import Interaction

from bot.cogs.polls.views.finalize_poll_view import FinalizePollView
from bot.cogs.polls.views.poll_view import PollView
from db import PollQuestion
from db.helpers import polls_helper


class CreatePollModal(nextcord.ui.Modal):
    def __init__(self, text: str = None):
        super().__init__(title='Create a Poll',
                         custom_id='create_poll_modal',
                         timeout=None)

        self.poll_text = nextcord.ui.TextInput(label='Poll Text',
                                               placeholder='Enter some text here...',
                                               max_length=1500,
                                               style=nextcord.TextInputStyle.paragraph,
                                               default_value=text,
                                               required=True)
        self.add_item(self.poll_text)

        self.choices = nextcord.ui.TextInput(label='Choices (one per line. Max 20)',
                                             placeholder='Enter choices here...',
                                             max_length=500,
                                             style=nextcord.TextInputStyle.paragraph,
                                             required=True)
        self.add_item(self.choices)

    async def callback(self, interaction: Interaction) -> None:
        poll_question = PollQuestion(text=self.poll_text.value,
                                     guild_id=interaction.guild.id,
                                     channel_id=interaction.channel_id,
                                     author_id=interaction.user.id,
                                     is_open=True)
        try:
            finalize_poll_view = FinalizePollView(poll_question)
            choice_strings = self.choices.value.split('\n')
            choices = polls_helper.create_choices_from_strings(choice_strings)
            if len(choices) < 1:
                raise ValueError('You must have at least 1 choice.')
            if len(choices) > 20:
                raise ValueError('You cannot have more than 20 choices.')
        except ValueError as e:
            await interaction.response.send_message(f'Error: {str(e)}', ephemeral=True)
            return
        poll_question.choices = choices
        poll_view = PollView(poll_question)
        content = f'**Preview**:\n{poll_view.content}\nTo finalize this poll, confirm a few settings.'
        await interaction.response.send_message(content=content,
                                                view=finalize_poll_view,
                                                ephemeral=True)
