from typing import List, Union

from sqlalchemy.orm import lazyload

from db import PollChoice, PollQuestion, DB, PollResponse


def search_open_polls(search: str) -> List[PollQuestion]:
    return DB.s.query(PollQuestion).filter(PollQuestion.text.ilike(f'%{search}%'), PollQuestion.is_open).all()


def create_choices_from_strings(choice_strings: List[str]) -> List['PollChoice']:
    choice_strings = [choice for choice in choice_strings if choice]  # Remove empty strings
    choices = [PollChoice(text=choice, ordinal=idx) for idx, choice in enumerate(choice_strings)]
    for choice in choices:
        choice.validate()
    return choices


def get_open_polls() -> List[PollQuestion]:
    return DB.s.all(PollQuestion, is_open=True)


def get_poll(poll_id: int) -> PollQuestion:
    return DB.s.query(PollQuestion).get(poll_id)


def get_poll_from_choice(choice_id: int) -> PollQuestion:
    return DB.s.query(PollQuestion).options(lazyload(PollQuestion.choices)).join(PollChoice).filter(PollChoice.id == choice_id).one()


def get_choice(choice_id: int) -> PollChoice:
    return DB.s.query(PollChoice).get(choice_id)


def get_poll_response(choice_id: int, respondent_id: int) -> PollResponse:
    return DB.s.query(PollResponse).options(lazyload(PollResponse.choice)).get((choice_id, respondent_id))


def get_responses_to_poll_for_respondent(respondent_id: int, poll_id: int) -> List[PollResponse]:
    return DB.s.query(PollResponse)\
        .join(PollChoice)\
        .join(PollQuestion)\
        .filter(PollResponse.respondent_id == respondent_id)\
        .filter(PollQuestion.id == poll_id)\
        .all()


def save(poll_model: Union[PollQuestion, PollChoice, PollResponse] = None):
    if poll_model and poll_model not in DB.s:
        DB.s.add(poll_model)
    DB.s.commit()


def delete(poll_model: Union[PollQuestion, PollChoice, PollResponse], commit=True):
    if poll_model in DB.s:
        DB.s.delete(poll_model)
    if commit:
        DB.s.commit()
