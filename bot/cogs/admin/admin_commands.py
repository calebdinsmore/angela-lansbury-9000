import nextcord
from nextcord import slash_command, Interaction
from nextcord.ext import commands

from bot.utils.constants import TESTING_GUILD_ID


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='summary',
                   description='Summary of guilds Angela has been added to.',
                   guild_ids=[TESTING_GUILD_ID])
    async def summary(self, interaction: Interaction):
        embed = nextcord.Embed()
        embed.add_field(name='Server Count', value=len(self.bot.guilds))
        guilds = '\n'.join([f'- {g.name}' for g in self.bot.guilds])
        embed.add_field(name='Servers', value=guilds, inline=False)
        await interaction.send(embed=embed)
