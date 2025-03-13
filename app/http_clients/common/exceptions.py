import asyncio
from functools import wraps
from typing import Callable

from aiohttp import ClientConnectionError


"""API client base exceptions are defined here."""


class APIError(RuntimeError):
    """Generic Urban API error."""


class APIConnectionError(APIError):
    """Could not connect to the API."""


class APITimeoutError(APIError, TimeoutError):
    """Timed out while awaiting response from UrbanAPI."""


class ObjectNotFoundError(APIError):
    """Given object is not found, therefore further calculations are impossible."""


class InvalidStatusCode(APIError):
    """Got unexpected status code from API request."""


def handle_exceptions(func: Callable) -> Callable:
    """
    This decorator is used to handle aiohttp exceptions
    and pass them into the middleware exception handler
    """

    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientConnectionError as exc:
            client = args[0]
            raise APIConnectionError(f"Error on connection by {client}") from exc
        except asyncio.exceptions.TimeoutError as exc:
            client = args[0]
            raise APITimeoutError(f"Timeout expired on {client} request") from exc

    return _wrapper
