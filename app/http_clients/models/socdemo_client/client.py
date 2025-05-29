"""
SocDemoClient is defined here for taking territories population pyramids
"""
from __future__ import annotations

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

    def __post_init__(self):
        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    def __str__(self):
        return "SocDemoClient"

    @handle_exceptions
    async def get_population_pyramid(self, territory_id: int, oktmo_code: int | None = None, year: int | None = None) -> tuple[list[int], list[int], list[str]]:
        """
        Args: territory_id, oktmo_code, year
        Returns: tuple with men,women, indexes lists
        where men[i] is amount of men who are indexes[i] years old
        """

        indicator_id = self.config.const_request_params["population_pyramid_indicator"]

        # getting response
        url = f"{self.config.host}/indicators/{indicator_id}/{territory_id}/detailed"

        params = {
            "territory_id": territory_id,
            "indicator_id": self.config.const_request_params["population_pyramid_indicator"],
        }

        if oktmo_code is not None:
            params["oktmo_code"] = oktmo_code

        if year is not None:
            params["year"] = year

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError(f"no population pyramid for territory {territory_id} with oktmo code {oktmo_code}, year {year}")

        pyramids = pd.DataFrame(data)
        year = year or max(pyramids["year"])
        pyramid = pyramids.loc[pyramids["year"] == year].iloc[0]

        # formatting

        men: list[int] = list()
        women: list[int] = list()
        indexes: list[str] = list()

        for item in pyramid["data"]:
            index_start = item["age_start"]
            # bad idea but we'll fix that
            index_end = item["age_end"] if item["age_end"] is not None else 130
            men_amount = int(item["male"]) if item["male"] is not None else 0
            women_amount = int(item["female"]) if item["female"] is not None else 0

            men.append(men_amount)
            women.append(women_amount)
            indexes.append(index_start if index_start == index_end else f"{index_start}-{index_end}")

        return men, women, indexes
