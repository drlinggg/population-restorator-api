import aiohttp

import json

from app.utils import logger
from .time import get_current_time

async def handle_request(url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}) -> json:
    """
    Returns response for given url, params & headers request
    """
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url=url, params=params) as response:
                #todo fix a little logger info
                logger.debug(
                        f'sent request {url} with params {params} and headers {headers}; status {response.status} {get_current_time()}'
                )
                return (await response.json())
        except aiohttp.ClientResponseError as e:
            logger.error(
                    f"failed to send request {url} with params {params} and headers {headers}; status {response.status} {get_current_time()}"
            )
            return None
