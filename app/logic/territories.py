"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pandas as pd
import structlog
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability, SurvivabilityCoefficients

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide
from population_restorator.scenarios import forecast as prforecast
from sqlalchemy import text

from app.db import PostgresConnectionManager
from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)
from app.utils import DBConfig, PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))


# add this to middleware and _postgres_conn
class TerritoriesService:
    # todo desc

    def __init__(self, dbconfig: DBConfig):
        self.db_config = dbconfig

    async def get_connect(self) -> None:
        self.connection_manager = PostgresConnectionManager(self.db_config, structlog.get_logger())
        await self.connection_manager.refresh()

    async def shut_connect(self) -> None:
        await self.connection_manager.shutdown()

    async def balance(self, territory_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        # todo desc

        urban_client = UrbanClient()

        internal_territories_df = await urban_client.get_internal_territories(territory_id)
        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)

        internal_houses_df, population, main_territory = await asyncio.gather(
            urban_client.get_houses_from_territories(territory_id),
            urban_client.get_population_from_territory(territory_id),
            urban_client.get_territory(territory_id),
        )

        # internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv")
        # internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv")

        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            main_territory,
            config.app.debug,
        )

    #
    async def divide(self, territory_id: int, houses_df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, ...]:
        # todo desc

        # i dont realy like this part

        socdemo_client = SocDemoClient()

        men, women, indexes = await socdemo_client.get_population_pyramid(territory_id)

        men = [x / sum(men) for x in men]
        women = [x / sum(women) for x in women]
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men, women)]

        distribution = SocialGroupsDistribution(primary, [])

        if houses_df is None:
            houses_df = (await self.balance(territory_id))[1]

        result = prdivide(houses_df, distribution=distribution, year=None, verbose=config.app.debug)

        return result

    async def restore(
        self,
        territory_id: int,
        survivability_coefficients: dict[str, tuple[float]],
        year_begin: int,
        years: int,
        boys_to_girls: float,
        fertility_coefficient: float,
        fertility_begin: int,
        fertility_end: int,
    ):
        """Lasciate ogne speranza, voi ch’entrate"""

        # example
        coeffs = SurvivabilityCoefficients(
            [1 / (i * 0.1) for i in range(1, 100)], [1 / (i * 0.1) for i in range(1, 100)]
        )

        divide_result = await self.divide(territory_id)

        forecast_result = prforecast(
            houses_db="/home/banakh/work/population-restorator-api/population-restorator/test.db",  # toberenamed
            coeffs=coeffs,
            year_begin=year_begin,
            years=years,
            boys_to_girls=boys_to_girls,
            fertility_coefficient=fertility_coefficient,
            fertility_begin=fertility_begin,
            fertility_end=fertility_end,
            verbose=config.app.debug,
        )

        # await self.get_connect()
        # something like that
        # statement = "select * from divide;"
        # async with self.connection_manager.get_connection() as conn:
        #    print((await conn.execute(text(statement))).mappings().all())
        # await conn.commit()
        # await self.shut_connect()

        return forecast_result  # mb
