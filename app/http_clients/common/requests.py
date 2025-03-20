from __future__ import annotations

import aiohttp
import structlog

from .exceptions import InvalidStatusCode


async def handle_request(url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}) -> dict | None:
    """
    Returns response for given url, params & headers request
    """

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params) as response:
            logger = structlog.get_logger()
            logger.info(
                f"sent request: {{request: {url}, params: {params}, headers: {headers}, status: {response.status} }}"
            )

            if response.status == 404:
                return None
            if response.status != 200:
                logger.error(f"error on get: {{ status: {response.status}, response_text: {await response.text()} }}")
                raise InvalidStatusCode(f"Unexpected status code on {url}, {params}: got {response.status}")

            return await response.json()
