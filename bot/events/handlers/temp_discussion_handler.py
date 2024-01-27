"""
A temporary handler specific to the October Bumpers Group
"""
import nextcord
from nextcord.ext import commands

REACTION_MESSAGE_ID = 1200285186483564634
REACTION_CHANNEL_ID = 1199455065715527752
REACTION_EMOJI = '👍'
ROLE_ID = 1200604278931333170


async def handle_closure_react(bot: commands.Bot, payload: nextcord.RawReactionActionEvent):
    if payload.message_id != REACTION_MESSAGE_ID:
        return
    if str(payload.emoji) != REACTION_EMOJI:
        return
    guild = nextcord.utils.get(bot.guilds, id=payload.guild_id)
    member = nextcord.utils.get(guild.members, id=payload.user_id)
    if member is None:
        return
    role = nextcord.utils.get(guild.roles, id=ROLE_ID)
    if role is None:
        return
    if payload.event_type == 'REACTION_ADD':
        await member.add_roles(role)
    elif payload.event_type == 'REACTION_REMOVE':
        await member.remove_roles(role)
