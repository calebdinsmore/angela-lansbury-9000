import nextcord


class SantaCsvModel:
    def __init__(self, dict_row: dict):
        self._nickname = None
        self.dont_match = dict_row.get('NoMatch', '').split(',')
        self.dont_match = [int(i) if i else None for i in self.dont_match]
        self.dont_match = list(filter(lambda x: x is not None, self.dont_match))
        self.dict_row = dict_row
        self.recipient = None
        self.id = None

    @property
    def username(self):
        return self.dict_row.get('What is your discord username?')

    @property
    def is_participating(self):
        value = self.dict_row.get('Would you like to participate in Secret Santa, a Christmas Card exchange, or both?')
        return value == 'Secret Santa' or value == 'Both'

    @property
    def intl_friendly(self):
        return self.dict_row.get('Are you willing/able to ship internationally if necessary?') == 'Yes'

    @property
    def country(self):
        return self.dict_row.get('Country')

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, nickname: str):
        self._nickname = nickname

    @property
    def answers_embed(self):
        excluded_headers = {
            'Timestamp',
            'NoMatch',
            'Country',
            'What is your discord username?',
            'What is your max budget for a gift exchange?',
            'Are you willing/able to ship internationally if necessary?',
            'Would you like to participate in Secret Santa, a Christmas Card exchange, or both?',
        }
        embed = nextcord.Embed(title=f'Your recipient: {self.dict_row.get("What is your discord username?")} '
                                     f'({self.nickname})',
                               description=f'Here are the questions and answers submitted by your gift recipient!')
        for question, answer in self.dict_row.items():
            if question in excluded_headers or not answer:
                continue
            embed.add_field(name=question, value=answer, inline=False)
        return embed

    def set_recipient(self, recipient_id):
        self.recipient = recipient_id

    def set_id(self, member_id: int):
        self.id = member_id
