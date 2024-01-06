import aiohttp
from typing import List
from api_service.core import HttpError
from api_service.duckling.parsed_values import ParsedValues


async def parse(text: str, tz: str = 'US/Eastern') -> List[ParsedValues]:
    url = 'http://68.183.96.166:8000/parse'
    payload = {
        'locale': 'en_US',
        'tz': tz,
        'text': text
    }
    response = await _post(url, payload)
    return [ParsedValues(value) for value in response]


async def _post(uri: str, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(uri, data=data) as resp:
            if resp.status < 300:
                return await resp.json()
            else:
                raise HttpError(uri, resp.status)
