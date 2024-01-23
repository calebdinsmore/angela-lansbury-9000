"""
A file that contains all the commands for the threads cog.
"""
import nextcord
from nextcord import slash_command, SlashOption
from nextcord.ext import commands

from bot.cogs.threads import threads_helpers


class ThreadsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name='threads')
    async def threads(self, interaction: nextcord.Interaction):
        pass

    @threads.subcommand(name='all', description='See all threads in this server.')
    async def post_threads_index(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        await interaction.send(embed=threads_helpers.build_index_embed(interaction.guild), ephemeral=True)

    @threads.subcommand(name='search', description='Search for a thread by name.')
    async def search(self, interaction: nextcord.Interaction, name: nextcord.Thread = SlashOption(name='name')):
        await interaction.send(f'Jump to thread: {name.mention}', ephemeral=True)

