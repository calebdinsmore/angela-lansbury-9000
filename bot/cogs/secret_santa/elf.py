"""
elf.py (Secret Santa's Helper)
"""
import csv
import os
import random
import sqlalchemy as sa
from collections import defaultdict
from typing import Dict, List

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from bot.cogs.secret_santa.santa_csv_model import SantaCsvModel
from bot.config import Config
from bot.utils import messages
from db import DB
from db.model.santa_participant import SantaParticipant


SMORE = 212416365317980171
MRS_SMORE = 466051914442997762


class MemberMatchError(Exception):
    failures: List[str]

    def __init__(self, failures):
        self.failures = failures


def try_to_get_member(csv_name: str, guild: nextcord.Guild):
    member = nextcord.utils.get(guild.members, name=csv_name.lower())
    if member is None:
        member = nextcord.utils.get(guild.members, nick=csv_name)
    if member is None:
        member = guild.get_member_named(csv_name)
    return member


def build_models_from_csv(guild: nextcord.Guild):
    models = {}
    filename = 'SecretSantaProd.csv' if Config().is_prod else 'SecretSantaTest.csv'
    failed_to_match = []
    with open(os.path.dirname(os.path.realpath(__file__)) + f'/static/{filename}') as santa_csv:
        reader = csv.DictReader(santa_csv)
        for row in reader:
            model = SantaCsvModel(row)
            if not model.is_participating:
                continue
            member = try_to_get_member(model.username, guild)
            if member is None:
                failed_to_match.append(model.username)
                # model.set_id(random.randint(0, 10000000))
                # models[model.id] = model
            else:
                model.set_id(member.id)
                model.nickname = member.display_name
                models[member.id] = model
    if failed_to_match:
        raise MemberMatchError(failed_to_match)
    return models


def generate_pairings(models: Dict[int, SantaCsvModel]) -> Dict[int, int]:
    pairing_dict = defaultdict(int)
    domestic_only = list(filter(lambda m: not m.intl_friendly, models.values()))
    for model in domestic_only:
        pool = list(filter(lambda r: r.id != model.id and r.country == model.country and r.id not in pairing_dict.values(),
                           models.values()))
        recipient = random.choice(pool)
        pairing_dict[model.id] = recipient.id
    remaining_ids = list(filter(lambda x: pairing_dict[x] == 0, models.keys()))
    for remaining_id in remaining_ids:
        pool = list(filter(lambda x: x != remaining_id and x not in pairing_dict.values(), models.keys()))
        if not pool:
            raise RuntimeError('No recipients remaining')
        pairing_dict[remaining_id] = random.choice(pool)
    test_pairings(models, pairing_dict)
    return pairing_dict


def test_pairings(models, pairing_dict):
    """
    Ensure all participants are accounted for and there aren't people paired to each other
    """
    remainder = list(filter(lambda x: x.id not in pairing_dict.values(), models.values()))
    assert len(remainder) == 0
    for santa_id, recipient_id in pairing_dict.items():
        if Config().is_prod:
            assert pairing_dict[recipient_id] != santa_id, 'Cyclic pairing found'
        if santa_id == SMORE:
            assert recipient_id != MRS_SMORE, 'Smores got matched'
        if santa_id == MRS_SMORE:
            assert recipient_id != SMORE, 'Smores got matched'
        if not models[santa_id].intl_friendly:
            assert models[santa_id].country == models[recipient_id].country, f'Failed intl check'
        assert models[santa_id].is_participating, 'Somehow found a non-participant'


def persist_pairings(pairing_dict: Dict[int, int]):
    for santa_id, recipient_id in pairing_dict.items():
        DB.s.add(SantaParticipant(santa_id=santa_id, recipient_id=recipient_id))
    DB.s.commit()


def clear_pairings():
    DB.s.execute(sa.delete(SantaParticipant).where(True))
    DB.s.commit()


async def handle_santa_message(bot: commands.Bot, interaction: Interaction, recipient_choice: str, message: str):
    ephemeral = interaction.guild is not None
    if recipient_choice not in ['Your Santa', 'Your Gift Recipient']:
        return await interaction.send(embed=messages.error('Invalid recipient choice.'))
    if recipient_choice == 'Your Santa':
        # pairing = DB.s.get_one(recipient_id=interaction.user.id)
        pairing = DB.s.first(SantaParticipant, recipient_id=interaction.user.id)
        if not pairing:
            return await interaction.send(
                embed=messages.error('Unable to find your Santa. Are you sure you\'re participating in Secret Santa?'))
        santa_id = pairing.santa_id
        santa_user = bot.get_user(santa_id)
        if not santa_user:
            return await interaction.send(
                embed=messages.error('Unable to message your Santa. Please report this to Smore!'))
        await santa_user.send(embed=messages.santa_message(message, interaction.user, show_name=True))
        await interaction.send(f'Message sent to your Santa!',
                               embed=messages.santa_message(message, interaction.user, show_name=True),
                               ephemeral=ephemeral)
        if ephemeral:
            await interaction.user.send('Message sent to your Santa!',
                                        embed=messages.santa_message(message, interaction.user, show_name=True))
    else:
        pairing = DB.s.first(SantaParticipant, santa_id=interaction.user.id)
        if not pairing:
            return await interaction.send(
                embed=messages.error(
                    'Unable to find your recipient. Are you sure you\'re participating in Secret Santa?'))
        recipient_id = pairing.recipient_id
        recipient_user = bot.get_user(recipient_id)
        if not recipient_user:
            return await interaction.send(
                embed=messages.error('Unable to message your recipient. Please report this to Smore!'))
        await recipient_user.send(embed=messages.santa_message(message, interaction.user))
        await interaction.send(f'Message sent to {recipient_user.display_name}!',
                               embed=messages.santa_message(message, interaction.user, show_name=True),
                               ephemeral=ephemeral)
        if ephemeral:
            await interaction.user.send(f'Message sent to {recipient_user.display_name}!',
                                        embed=messages.santa_message(message, interaction.user, show_name=True))


async def send_recipient_embeds(bot: commands.Bot, guild: nextcord.Guild):
    models = build_models_from_csv(guild)
    pairings = DB.s.all(SantaParticipant)
    for pairing in pairings:
        santa = bot.get_user(pairing.santa_id)
        recipient_csv_model = models.get(pairing.recipient_id)
        if not recipient_csv_model:
            return await bot.get_user(212416365317980171).send(embed=messages.error('Something went wrong!'))
        await santa.send(embed=recipient_csv_model.answers_embed)


async def mark_sent(bot: commands.Bot, santa_id: int, tracking_info: str):
    pairing = DB.s.first(SantaParticipant, santa_id=santa_id)
    recipient = bot.get_user(pairing.recipient_id)
    pairing.has_shipped = True
    DB.s.commit()
    shipment_message = '**Your Santa has shipped your gift!**'
    shipment_message += f'\n\nThey provided the following tracking info: {tracking_info}'
    await recipient.send(shipment_message)


async def send_reminders(bot: commands.Bot):
    unsent_pairings = DB.s.query(SantaParticipant).filter_by(has_shipped=False)
    for pairing in unsent_pairings:
        santa = bot.get_user(pairing.santa_id)
        await santa.send(':wave: Hi! According to my records, you haven\'t sent your gift yet. Friendly reminder to '
                         'send it out and mark it sent with `/santa mark-sent`!')


def pairings_embed():
    pairings = DB.s.all(SantaParticipant)
    description = ''
    for pairing in pairings:
        if pairing.santa_id == 212416365317980171:
            description += f'<@{pairing.santa_id}> => <@{pairing.recipient_id}>\n'
        else:
            description += f'||<@{pairing.santa_id}>|| => <@{pairing.recipient_id}>\n'
    return nextcord.Embed(title='Pairings', description=description)
