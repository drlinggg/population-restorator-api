import json
from dataclasses import dataclass

import aiohttp

from app.utils import logger

from .time import get_current_time


@dataclass
class BaseHandleResult:
    """todo"""

    response: dict | None = None

    def is_success(self) -> bool:
        pass


@dataclass
class SuccessHandle(BaseHandleResult):
    """todo"""

    def is_success(self) -> bool:
        return True


@dataclass
class FailedToConnect(BaseHandleResult):
    """todo"""

    def is_success(self) -> bool:
        return False


@dataclass
class FailedToGetResponse(BaseHandleResult):
    """todo"""

    def is_success(self) -> bool:
        return False


async def handle_request(url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}) -> BaseHandleResult:
    """
    Returns response for given url, params & headers request
    """

    session = aiohttp.ClientSession(headers=headers)

    try:
        response = await session.get(url=url, params=params)
        logger.debug(f"sent request {url} with params {params} and headers {headers}; status {response.status}")
        response.raise_for_status()
        return SuccessHandle(await response.json())
    except aiohttp.ClientResponseError as e:
        logger.error(f"failed to send request {url} with params {params} and headers {headers}; status {e.status}")
        return FailedToGetResponse()
    except aiohttp.ClientError as e:
        logger.error(f"failed to connect to {url}: {e}")
        return FailedToConnect()
    finally:
        await session.close()
