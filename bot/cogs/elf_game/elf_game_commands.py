from nextcord.ext import commands, tasks


class ElfGameCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_for_new_elves.start()

    @tasks.loop(minutes=1)
    async def check_for_new_elves(self):
        if not self.bot.is_ready():
            return
        for guild in self.bot.guilds:
            pass
