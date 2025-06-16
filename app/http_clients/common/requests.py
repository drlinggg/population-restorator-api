"""
Sending request method is defined here
"""

from __future__ import annotations

from typing import Any

import aiohttp
import structlog

from .exceptions import InvalidStatusCode


async def _handle_request(
    method: str,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    session: aiohttp.ClientSession | None = None,
    json: dict | None = None,
) -> dict | None:
    """
    handles HTTP requests (GET, POST, DELETE) and returns response
    """
    params = params or {}
    headers = headers or {}
    logger = structlog.get_logger()

    new_session = session is None
    if new_session:
        session = aiohttp.ClientSession()

    try:
        async with session.request(
            method=method.upper(), url=url, params=params, json=json, headers=headers
        ) as response:
            logger.info(
                f"Sent request: {{method: {method}, url: {url}, "
                f"params: {params}, headers: {headers}, status: {response.status}}}"
            )
            logger.debug(f"Response headers: {response.headers}")

            if response.status == 404:
                return None
            if response.status == 204:
                return None
            if response.status >= 200 and response.status < 300:
                return await response.json()

            response_text = await response.text()
            logger.error(f"Error on {method}: {{status: {response.status}, " f"response_text: {response_text}}}")
            #raise InvalidStatusCode(f"Unexpected status code on {url}: {response.status}")
    finally:
        if new_session and session:
            await session.close()


async def handle_get_request(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict | None:
    return await _handle_request("GET", url, params, headers, session=session)


async def handle_post_request(
    url: str,
    json: dict,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict | None:
    return await _handle_request("POST", url, params, headers, session, json)


async def handle_delete_request(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    session: aiohttp.ClientSession | None = None,
    json: dict | None = None,
) -> dict | None:
        return await _handle_request("DELETE", url, params, headers, session=session, json=json)
