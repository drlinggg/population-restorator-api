import json
import os
import uuid

import aiohttp
import structlog

from app.utils import PopulationRestoratorApiConfig

from .exceptions import InvalidStatusCode


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()


async def handle_request(url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}) -> dict:
    """
    Returns response for given url, params & headers request
    """

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as session:
        async with session.get(url=url, params=params) as response:
            logger.info(f"sent request {url} with params {params} and headers {headers}; status {response.status}")

            if response.status == 404:
                return None
            if response.status != 200:
                logger.error(f"error on get, {response.status}, {await response.text()}")
                raise InvalidStatusCode(f"Unexpected status code on {url}, {params}: got {response.status}")

            return await response.json()
