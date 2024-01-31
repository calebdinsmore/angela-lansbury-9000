import nextcord
import sentry_sdk
from nextcord.ext import commands

from bot.cogs import AutoDeleteCommands, ImageMessageDeleteCommands
from bot.cogs.activity.activity_commands import ActivityCommands
from bot.cogs.admin.admin_commands import AdminCommands
from bot.cogs.birthday.birthday_commands import BirthdayCommands
from bot.cogs.server_admin.server_admin_commands import ServerAdminCommands
from bot.cogs.threads.threads_commands import ThreadsCommands
from bot.config import Config
from bot.events import on_member_join_event, on_guild_join_event, on_raw_reaction_add_event, \
    on_raw_reaction_remove_event
from bot.events.on_message_event import register_event
from bot.utils import logger

intents = nextcord.Intents.all()
config = Config()
bot = commands.Bot(intents=intents)

if config.is_prod:
    sentry_sdk.init(
        dsn="https://00565c13fed21a6b54e808aad5acaea1@o250406.ingest.sentry.io/4505959527284736",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
else:
    sentry_sdk.init(dsn='')


@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.CustomActivity(name='Ringing in the New Year 🎉'))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


def run():
    bot.add_cog(AutoDeleteCommands(bot))
    bot.add_cog(ImageMessageDeleteCommands(bot))
    bot.add_cog(ActivityCommands(bot))
    bot.add_cog(BirthdayCommands(bot))
    bot.add_cog(AdminCommands(bot))
    bot.add_cog(ThreadsCommands(bot))
    bot.add_cog(ServerAdminCommands())
    logger.register_bot(bot)
    on_member_join_event.register_event(bot)
    on_guild_join_event.register_event(bot)
    on_raw_reaction_add_event.register_event(bot)
    on_raw_reaction_remove_event.register_event(bot)
    register_event(bot)
    bot.run(config.BOT_TOKEN)

