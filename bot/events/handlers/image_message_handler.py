import datetime as dt
import nextcord
import sentry_sdk
from nextcord.ext import commands

from bot.utils.constants import DO_APRIL_FOOLS
from bot.utils.messages import message_has_image
from bot.views.delete_image import DeleteImage
from db import ImageMessageToDelete, DB
from db.helpers import image_message_helper, user_settings_helper, guild_config_helper


def bot_has_necessary_permissions(message: nextcord.Message):
    bot_member = message.guild.me
    channel_perms = message.channel.permissions_for(bot_member)
    checks = [
        channel_perms.manage_messages,
        channel_perms.read_message_history,
        channel_perms.send_messages
    ]
    return all(checks)


async def image_message_handler(message: nextcord.Message):
    if message.guild is None:
        return
    if not message_has_image(message):
        return
    if not bot_has_necessary_permissions(message):
        return
    guild_config = guild_config_helper.get_guild_config(message.guild.id)
    if guild_config is not None and not guild_config.image_deletion_prompts_enabled:
        return
    view = DeleteImage()
    try:
        user_settings = user_settings_helper.get_user_settings(message.author.id, message.guild.id)
        if not user_settings.image_deletion_prompts_enabled:
            # user has disabled image prompts
            return
        user_channel_delete_settings = image_message_helper.get_user_channel_delete_settings(message.guild.id,
                                                                                             message.channel.id,
                                                                                             message.author.id)
        if user_channel_delete_settings is not None:
            # User has delete settings set for this channel, skip the prompt
            if user_channel_delete_settings == 0:
                # User channel delete settings are set to keep, ignore the prompt and don't set image to delete
                return
            mark_image_for_deletion(message, user_channel_delete_settings)
            return
        text_content = '📸 I noticed you sent an image/video. Want me to delete it after a number of days?'
        if DO_APRIL_FOOLS:
            text_content = '🪨 **The Boulder** noticed you sent an image/video. Should **The Boulder** ' \
                           'destroy it after a number of days?'
        prompt = await message.reply(
            text_content,
            view=view)
        await view.wait()
        await prompt.delete()
    except nextcord.Forbidden:
        sentry_sdk.capture_message(f'Got Forbidden error for channel [{message.channel.name}] '
                                   f'in guild [{message.guild.name}]')
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
