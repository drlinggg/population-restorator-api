from __future__ import annotations

import asyncio
import os

import pandas as pd
import structlog
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide

from app.db import PostgresConnectionManager
from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)
from app.utils import PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))

from sqlalchemy import text


# add this to middleware and _postgres_conn
class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        # todo desc

        urban_client = UrbanClient()

        internal_territories_df = await urban_client.get_internal_territories(territory_id)
        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)

        internal_houses_df, population = await asyncio.gather(
            urban_client.get_houses_from_territories(territory_id),
            urban_client.get_population_from_territory(territory_id),
        )

        internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv", index=False)
        internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv", index=False)

        # 545,555 error sys1 exit
        return prbalance(
            100000,
            internal_territories_df,
            internal_houses_df,
            config.app.debug,
        )

    async def divide(self, territory_id: int, houses_df: pd.DataFrame | None = None):
        # todo desc

        socdemo_client = SocDemoClient()

        men, women, indexes = await socdemo_client.get_population_pyramid(territory_id)

        men = [x / sum(men) for x in men]
        women = [x / sum(women) for x in women]
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men, women)]

        distribution = SocialGroupsDistribution(primary, list())

        result = list()

        if houses_df is None:
            houses_df = (await self.balance(territory_id))[1]
            result = prdivide(houses_df, distribution=distribution, year=None, verbose=config.app.debug)

        result = prdivide(houses_df, distribution=distribution, year=None, verbose=config.app.debug)

        return result

        connection = PostgresConnectionManager(config.db, structlog.get_logger())
        await connection.refresh()

        # something like that
        # statement = "select * from test;"
        # async with connection.get_connection() as conn:
        #    print((await conn.execute(text(statement))).mappings().all())
        # await conn.commit()

        await connection.shutdown()

    async def restore(self, territory_id: int):
        # todo
        pass
