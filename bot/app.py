import nextcord
import sentry_sdk
from nextcord.ext import commands

from bot.cogs import AutoDeleteCommands, ImageMessageDeleteCommands
from bot.config import Config
from bot.events.on_message_event import register_event

intents = nextcord.Intents.all()
config = Config()
bot = commands.Bot(intents=intents)

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


@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Game(name='a role in every movie'))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


def run():
    bot.add_cog(AutoDeleteCommands(bot))
    bot.add_cog(ImageMessageDeleteCommands(bot))
    register_event(bot)
    bot.run(config.BOT_TOKEN)

