import datetime as dt
import nextcord
import sentry_sdk

from bot.utils.messages import message_has_image
from bot.views.delete_image import DeleteImage
from db import ImageMessageToDelete, DB


async def image_message_handler(message: nextcord.Message):
    if not message_has_image(message):
        return
    view = DeleteImage()
    try:
        prompt = await message.reply(
            '📸 I noticed you sent an image/video. Want me to delete it after a number of days?',
            view=view)
        await view.wait()
        await prompt.delete()
    except Exception as e:
        sentry_sdk.capture_exception(e)
    if view.value is not None:
        mark_image_for_deletion(message, view.value)


def mark_image_for_deletion(message_to_delete: nextcord.Message, delete_after: int):
    delete_after_dt = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=delete_after)
    image_message_to_delete = ImageMessageToDelete(guild_id=message_to_delete.guild.id,
                                                   channel_id=message_to_delete.channel.id,
                                                   message_id=message_to_delete.id,
                                                   author_id=message_to_delete.author.id,
                                                   delete_after=delete_after_dt)
    DB.s.add(image_message_to_delete)
    DB.s.commit()
