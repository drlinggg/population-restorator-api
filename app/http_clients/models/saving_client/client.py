"""
This class is used for saving data to foreign api
with information about population, houses & territories
"""

from __future__ import annotations

import structlog

from app.http_clients.common import (
    BaseClient,
    handle_exceptions,
    handle_request,
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
    async def post_forecasted_data(
        self,
        houses_data: list[UrbanSocialDistribution]
    ):
        """
        Args: houses_data

        Returns: None
        """

        houses_data = [UrbanSocialDistributionPost.from_model(house)
                       for house in houses_data]

        url = f"{self.config.host}api/v1/distribution/create-many"
        params = {
            "dtos": houses_data
        }
        headers = {
            "accept": "application/json",
        }

        await handle_request(url=url, params=params, headers=headers)

