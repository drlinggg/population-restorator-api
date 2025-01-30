import aiohttp


async def handle_request(url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}) -> aiohttp.ClientResponse:
    """
    Returns response for given url, params & headers request
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url=url, params=params) as response:
                return response
        except aiohttp.ClientError as e:
            # log
            pass
