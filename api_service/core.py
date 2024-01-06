import aiohttp


async def get(uri: str, headers: dict = None):
    if not headers:
        headers = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(uri, headers=headers) as resp:
            if resp.status < 300:
                return await resp.json()
            else:
                raise HttpError(uri, resp.status)


class HttpError(Exception):
    def __init__(self, uri: str, code: int, reason: str = ''):
        self.message = f'HTTP returned {code} for: {uri} with reason: {reason}'
        self.code = code
        self.uri = uri

    def __str__(self):
        return self.message
