"""
SocDemoClient is defined here for taking territories population pyramids
"""

import os

import pandas as pd
import structlog

from app.http_clients.common import (
    BaseClient,
    ObjectNotFoundError,
    handle_exceptions,
    handle_request,
)
from app.utils import ApiConfig, PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()


class SocDemoClient(BaseClient):

    def __init__(self):
        self.config: ApiConfig | None = config.socdemo_api

        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    async def is_alive(self) -> bool:

        url = f"{self.config.host}/health_check/ping"
        result = await handle_request(url)
        if result:
            return True
        return False

    def __str__(self):
        return "SocDemoClient"

    @handle_exceptions
    async def get_population_pyramid(self, territory_id: int) -> tuple[list[int], list[int], list[str]]:
        """
        Args: territory_id
        Returns: tuple with men,women, indexes lists
        where men[i] is amount of men who are indexes[i] years old
        """

        indicator_id: str = "2"  # for populaion

        # getting response

        url = f"{self.config.host}/indicators/{indicator_id}/{territory_id}/detailed"

        params = {
            "territory_id": territory_id,
            "indicator_id": indicator_id,
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        pyramids = pd.DataFrame(data)
        latest_pyramid = pyramids.loc[pyramids["year"] == max(pyramids["year"])].iloc[0]

        # formatting

        men: list[int] = list()
        women: list[int] = list()
        indexes: list[str] = list()

        for item in latest_pyramid["data"]:
            index_start = item["age_start"]
            # bad idea but we'll fix that
            index_end = item["age_end"] if item["age_end"] is not None else 130
            men_amount = int(item["male"]) if item["male"] is not None else 0
            women_amount = int(item["female"]) if item["female"] is not None else 0

            men.append(men_amount)
            women.append(women_amount)
            indexes.append(index_start if index_start == index_end else f"{index_start}-{index_end}")

        return men, women, indexes
