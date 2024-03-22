import nextcord.ui

from bot.cogs.polls.views.util import add_new_response_or_remove_existing, remove_all_but_new_response, \
    confirmation_message, update_poll_message
from db.helpers import polls_helper


class PollChoiceButton(nextcord.ui.Button):
    async def callback(self, interaction: nextcord.Interaction):
        custom_id = interaction.data.get('custom_id', None)
        if custom_id:
            await interaction.response.defer()
            _, choice_id = custom_id.split(':')
            choice_id = int(choice_id)

            add_new_response_or_remove_existing(choice_id, interaction.user.id)

            selected_choice = polls_helper.get_choice(choice_id)
            if not selected_choice.question.is_multi_choice:
                remove_all_but_new_response(interaction.user.id, selected_choice.question_id, choice_id)

            await update_poll_message(selected_choice.question.id, interaction.channel)
            confirmation_content = confirmation_message(interaction.user.id, selected_choice.question_id)
            await interaction.send(confirmation_content, ephemeral=True)
