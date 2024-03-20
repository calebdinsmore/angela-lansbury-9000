from db import PollResponse
from db.helpers import polls_helper


def remove_all_but_new_response(respondent_id: int, question_id: int, choice_id: int):
    all_responses = polls_helper.get_responses_to_poll_for_respondent(respondent_id, question_id)
    for response in all_responses:
        if response.choice_id != choice_id:
            polls_helper.delete(response, commit=False)
    polls_helper.save()


def add_new_response_or_remove_existing(choice_id: int, user_id: int):
    poll_response = polls_helper.get_poll_response(choice_id, user_id)
    if not poll_response:
        poll_response = PollResponse(choice_id=choice_id, respondent_id=user_id)
        polls_helper.save(poll_response)
    else:
        polls_helper.delete(poll_response)


def confirmation_message(user_id: int, poll_id: int):
    all_responses_for_user = polls_helper.get_responses_to_poll_for_respondent(user_id,
                                                                               poll_id)
    confirmation_content = 'Your response has been recorded.'
    if all_responses_for_user:
        confirmation_content += '\nYour responses to this poll are: \n```\n' + '\n'.join(
            [response.choice.text for response in all_responses_for_user]) + '\n```'
    else:
        confirmation_content += '\nYou have not selected any options.'
    return confirmation_content


async def update_poll_message(poll_id: int, channel):
    from bot.cogs.polls.views.poll_view import PollView
    poll = polls_helper.get_poll(poll_id)
    poll_view = PollView(poll)
    if poll.message_id:
        message = await channel.fetch_message(poll.message_id)
        await message.edit(content=poll_view.content, embed=poll_view.results_embed, view=poll_view)
