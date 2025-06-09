"""
This class is used for saving data to foreign api
with information about population, houses & territories
"""

from __future__ import annotations

from asyncio import Semaphore, gather

import aiohttp
import structlog

from app.http_clients.common import (
    BaseClient,
    handle_delete_request,
    handle_exceptions,
    handle_post_request,
)
from app.models import UrbanSocialDistribution
from app.schemas import UrbanSocialDistributionPost, UrbanSocialDistributionDelete


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
    async def post_forecasted_data(self, houses_data: list[UrbanSocialDistribution]):
        houses_data = [UrbanSocialDistributionPost.from_model(house).dict() for house in houses_data]

        url = f"{self.config.host}/api/v1/distribution/create-many"
        headers = {
            "accept": "application/json",
        }

        await handle_post_request(url=url, headers=headers, json={"dtos": houses_data})

    @handle_exceptions
    async def delete_forecasted_data(
        self,
        houses_data: list[UrbanSocialDistribution],
    ):
        houses_data = [UrbanSocialDistributionDelete.from_model(house) for house in houses_data]
        base_url = f"{self.config.host}/api/v1/distribution/"
        session = aiohttp.ClientSession()
        semaphore = Semaphore(30)
        async def fetch_with_semaphore(url: str, params: dict, session):
            async with semaphore:
                return await handle_delete_request(url=url, params=params, session=session)

        tasks = [
            fetch_with_semaphore(url=base_url + str(house.building_id), params=house.dict(), session=session) for house in houses_data
        ]
        await gather(*tasks)
        await session.close()
