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
    handle_get_request,
)
from app.models import BirthStats, FertilityInterval, PopulationPyramid, SurvivabilityCoefficients
from app.utils import PopulationRestoratorApiConfig


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
    async def get_population_pyramid(
        self, territory_id: int, oktmo_code: int | None = None, year: int | None = None
    ) -> PopulationPyramid:
        """
        Args:
            territory_id: (int), id of the current territory in urban_api
            oktmo_code: (int|None), oktmo code of give territory, used in searching as additional argument ex. 79600000
            year: (int|None), the latest possible year to be searched for, if None then used the latest pyramid
        Returns: PopulationPyramid where men[age], women[age] amount of people with such sex and age
        """

        indicator_id = self.config.const_request_params["population_pyramid_indicator"]

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

        # getting response
        url = f"{self.config.host}/indicators/{indicator_id}/{territory_id}/detailed"
        data = await handle_get_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError(
                f"no population pyramids for territory {territory_id} with oktmo code {oktmo_code}, year {year}"
            )

        pyramids = pd.DataFrame(data)
        year = year or max(pyramids["year"])
        pyramid = pyramids.loc[pyramids["year"] == year].iloc[0]

        # formatting
        men: list[int] = []
        women: list[int] = []

        for item in pyramid["data"]:
            age_start, age_end = (
                int(item["age_start"]),
                int(item["age_end"]) if item["age_end"] is not None else item["age_start"],
            )
            if age_start >= 100:
                continue
            male = int(item["male"]) if item["male"] is not None else 0
            female = int(item["female"]) if item["female"] is not None else 0
            if age_start == age_end:
                men.append(male)
                women.append(female)
            else:
                for age in range(age_start, age_end + 1):
                    men.append(int(male / (age_end + 1 - age_start)))
                    women.append(int(female / (age_end + 1 - age_start)))

        return PopulationPyramid(men=men, women=women, year=year)

    async def get_surviability_coeffs_from_last_pyramids(
        self, territory_id: int, oktmo_code: int | None = None, year: int | None = None
    ) -> SurvivabilityCoefficients:
        """
        Args:
            territory_id: (int), id of the current territory in urban_api
            oktmo_code: (int|None), oktmo code of give territory, used in searching as additional argument ex. 79600000
            year: (int|None), the latest possible year to be searched for, if None then used the latest pyramid
        Returns: SurvivabilityCoefficients
                where men[age], women[age] is relative change of TODO HERe
        """

        after_pyramid = await self.get_population_pyramid(territory_id, oktmo_code, year)
        before_pyramid = await self.get_population_pyramid(territory_id, oktmo_code, after_pyramid.year - 1)

        if not (
            len(after_pyramid.men)
            == len(after_pyramid.women)
            == len(before_pyramid.men)
            == len(before_pyramid.women)
            == 100
        ):
            raise ObjectNotFoundError("some of pyramids have less/more than 100 ages")

        changes_men, changes_women = [], []
        for age in range(1, 100):
            changes_men.append((after_pyramid.men[age] / before_pyramid.men[age - 1]))
            changes_women.append((after_pyramid.women[age] / before_pyramid.women[age - 1]))
        changes_women.append(changes_women[-1])
        changes_men.append(changes_men[-1])
        return SurvivabilityCoefficients(men=changes_men, women=changes_women, year=after_pyramid.year)

    async def get_birth_stats(
        self,
        territory_id: int,
        fertility_interval: FertilityInterval,
        oktmo_code: int | None = None,
        year: int | None = None,
    ) -> BirthStats:
        """
        Args:
            territory_id: (int), id of the current territory in urban_api
            oktmo_code: (int|None), oktmo code of give territory, used in searching as additional argument ex. 79600000
            year: (int|None), the latest possible year to be searched for, if None then used the latest pyramid
        Retuns:
            BirthStats
        """

        population_pyramid = await self.get_population_pyramid(territory_id, oktmo_code, year)

        births = population_pyramid.men[0] + population_pyramid.women[0]
        fertil_women = sum(population_pyramid.women[fertility_interval.start : fertility_interval.end + 1])

        boys_to_girls_ratio = population_pyramid.men[0] / population_pyramid.women[0]
        return BirthStats(
            fertility_interval=fertility_interval,
            boys_to_girls=boys_to_girls_ratio,
            fertility_coefficient=births / fertil_women,
        )
