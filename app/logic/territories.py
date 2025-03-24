"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import os

import pandas as pd
import structlog
from sqlalchemy import text

from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide

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
            urban_client.get_territory(territory_id)
        )

        #internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv")
        #internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv")

        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            main_territory,
            config.app.debug,
        )

    #
    async def divide(self, territory_id: int, houses_df: pd.DataFrame | None = None):
        # todo desc

        socdemo_client = SocDemoClient()

        men, women, indexes = await socdemo_client.get_population_pyramid(territory_id)

        men = [x / sum(men) for x in men]
        women = [x / sum(women) for x in women]
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men, women)]

        distribution = SocialGroupsDistribution(primary, [])

        result = []
        if houses_df is None:
            houses_df = (await self.balance(territory_id))[1]
            result = prdivide(houses_df, distribution=distribution, year=None, verbose=config.app.debug)

        else:
            print(houses_df)
            result = prdivide(houses_df, distribution=distribution, year=None, verbose=config.app.debug)

        #await self.get_connect()
        # something like that
        #statement = "select * from divide;"
        #async with self.connection_manager.get_connection() as conn:
        #    print((await conn.execute(text(statement))).mappings().all())
        #await conn.commit()
        #await self.shut_connect()

        return result

    async def restore(self, territory_id: int):
        # todo
        pass
