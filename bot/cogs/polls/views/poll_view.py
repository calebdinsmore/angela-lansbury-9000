import nextcord.ui

from bot.cogs.polls.views.components.poll_choice_button import PollChoiceButton
from bot.cogs.polls.views.components.poll_choice_string_select import PollChoiceStringSelect
from db import PollQuestion


class PollView(nextcord.ui.View):
    def __init__(self, poll_question: PollQuestion):
        super().__init__(timeout=None)

        self.poll_question = poll_question

        self.choice_select = None
        if not poll_question.is_open:
            self.stop()
            return
        if len(poll_question.choices) > 5:
            placeholder = 'Select one or more...' if poll_question.is_multi_choice else 'Select one...'
            max_values = 1 if not poll_question.is_multi_choice else len(poll_question.choices)
            self.choice_select = PollChoiceStringSelect(placeholder=placeholder,
                                                        max_values=max_values,
                                                        custom_id=f'poll_choice_select:{poll_question.id}',
                                                        options=[nextcord.SelectOption(label=choice.text,
                                                                                       value=choice.id)
                                                                 for choice in poll_question.choices])
            self.add_item(self.choice_select)
        else:
            for choice in poll_question.choices:
                self.add_item(PollChoiceButton(label=choice.text,
                                               style=nextcord.ButtonStyle.secondary,
                                               custom_id=f'poll_choice_button:{choice.id}'))

    @property
    def content(self):
        closed = ' (Closed)' if not self.poll_question.is_open else ''
        content = f"""
### Poll 🗳️{closed}
{self.poll_question.text}\n⎯⎯
        """
        return content

    @property
    def results_embed(self):
        all_count = sum(len(choice.responses) for choice in self.poll_question.choices)
        anonymous = 'Results are anonymous.' if self.poll_question.is_anonymous else 'Results are not anonymous.'
        multiselect = 'You may select more than one option.' if self.poll_question.is_multi_choice else ''
        embed = nextcord.Embed(description=f'{all_count} total votes',
                               color=nextcord.Color.blurple())
        embed.set_footer(text=f'{anonymous} {multiselect}')
        for choice in self.poll_question.choices:
            count = len(choice.responses)
            if count == 0:
                continue
            embed.add_field(name=choice.text,
                            value=f'{choice_field_value(choice, choice.question.is_anonymous, count)}\n{count / all_count * 100:.2f}%')
        return embed


def choice_field_value(choice, is_anonymous: bool, count: int):
    if is_anonymous:
        return f'{count} vote{"s" if count != 1 else ""}'
    first_three_responses = ', '.join(f'<@{response.respondent_id}>' for response in choice.responses[:3])
    count_remaining = count - 3 if count > 3 else 0
    count_remaining = f' + {count_remaining} more' if count_remaining > 0 else ''
    return f'{first_three_responses}{count_remaining}'

