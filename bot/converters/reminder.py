from datetime import datetime, timedelta
from typing import List

from nextcord.ext import commands
from nextcord.ext.commands import CommandError
from sentry_sdk import capture_exception
import pytz

from api_service import HttpError
from api_service.duckling import duckling_service


class Reminder:
    def __init__(self, reminder_text: str, times: List[datetime]):
        self.reminder_text = reminder_text
        self.times = times

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):
        try:
            parsed_values = await duckling_service.parse(argument)
            if not parsed_values:
                raise CommandError('Could not parse any dates/times from message.')
        except HttpError as e:
            capture_exception(e)
            raise CommandError('Could not parse date from message (Duckling Error).')
        parsed_times = []
        for parsed_value in parsed_values:
            if parsed_value.dim == 'time':
                parsed_times.append(parsed_value)
        if not parsed_times:
            raise CommandError('Could not parse any dates/times from message.')
        # times = [datetime.now().astimezone(pytz.timezone('UTC')) + timedelta(seconds=30)]
        times = []
        for parsed_time in parsed_times:
            # 2021-02-14T17:00:00.000-08:00
            parsed_datetime = datetime.strptime(parsed_time.value.time_value, '%Y-%m-%dT%H:%M:%S.%f%z')
            times.append(parsed_datetime.astimezone(pytz.timezone('UTC')))
        times.sort()
        return cls(argument, times)
