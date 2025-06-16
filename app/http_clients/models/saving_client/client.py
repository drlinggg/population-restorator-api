"""
This class is used for saving data to foreign api
with information about population, houses & territories
"""

from __future__ import annotations

from asyncio import Semaphore, gather
from collections.abc import Iterable
from typing import Literal
from math import ceil

import aiohttp
import structlog

from app.http_clients.common import (
    BaseClient,
    handle_delete_request,
    handle_exceptions,
    handle_post_request,
)
from app.models import UrbanSocialDistribution
from app.schemas import UrbanSocialDistributionPost


logger = structlog.getLogger()


class SavingClient(BaseClient):
    """Saving API client that uses HTTP/HTTPS as transport."""

    def __post_init__(self):
        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    def __str__(self):
        return "SavingClient"

    @handle_exceptions
    async def post_forecasted_data(self, houses_data: Iterable[UrbanSocialDistribution]):
        houses_data = [UrbanSocialDistributionPost.from_model(house).dict() for house in houses_data]
        chunk_size = 1000
        semaphore_size = 10
        chunks_count = ceil(len(houses_data) / chunk_size)
        semaphore = Semaphore(semaphore_size)

        url = f"{self.config.host}/api/v1/distribution/create-many"
        headers = {
            "accept": "application/json",
        }
        session = aiohttp.ClientSession()

        async def send_chunk(chunk_id):
            start_idx = chunk_id * chunk_size
            end_idx = min((chunk_id + 1) * chunk_size, len(houses_data))
            chunk_data = houses_data[start_idx:end_idx]
            async with semaphore:
                await handle_post_request(
                    url=url,
                    headers=headers,
                    json={"dtos": chunk_data},
                    session=session
                )
                logger.info(f"Sent {chunk_id} chunk of {chunks_count}")

        tasks = [
            send_chunk(chunk_id)
            for chunk_id in range(chunks_count)
        ]

        await gather(*tasks)
        await session.close()

    @handle_exceptions
    async def delete_forecasted_data(
        self,
        scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"],
        buildings_ids: dict[int, set[int]],
    ):

        base_url = f"{self.config.host}/api/v1/distribution/many"

        params = {
            "scenario": scenario
        }

        session = aiohttp.ClientSession()

        tasks = [
            handle_delete_request(
                url=base_url,
                params=params | {"year": year},
                session=session,
                json=list(values),
            )
            for year, values in buildings_ids.items()
        ]
        await gather(*tasks)
        await session.close()
