from typing import List

import nextcord.ui

from bot.cogs.polls.views.util import update_poll_message
from db import PollResponse
from db.helpers import polls_helper


class PollChoiceStringSelect(nextcord.ui.StringSelect):
    async def callback(self, interaction: nextcord.Interaction):
        values: List[str] = interaction.data.get('values', [])
        poll_id = interaction.data.get('custom_id', None)
        if poll_id:
            await interaction.response.defer()
            _, poll_id = poll_id.split(':')
            poll_id = int(poll_id)
        else:
            return
        int_values = [int(value) for value in values]
        for choice_id in int_values:
            existing = polls_helper.get_poll_response(choice_id, interaction.user.id)
            if not existing:
                new = PollResponse(choice_id=choice_id, respondent_id=interaction.user.id)
                polls_helper.save(new)
        all_responses = polls_helper.get_responses_to_poll_for_respondent(interaction.user.id, poll_id)
        for response in all_responses:
            if response.choice_id not in int_values:
                polls_helper.delete(response, commit=False)
        polls_helper.save()
        await update_poll_message(poll_id, interaction.channel)
        # await interaction.send('Your response has been recorded.', ephemeral=True)
