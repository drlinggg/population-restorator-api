from __future__ import annotations

import os

import pandas as pd
import rq

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide

from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)
from app.utils import PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))


class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        """ """

        urban_client = UrbanClient()

        internal_territories_df = await urban_client.get_internal_territories(territory_id)
        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)
        internal_houses_df = await urban_client.get_houses_from_territories(territory_id)
        population = await urban_client.get_population_from_territory(territory_id)

        #internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv", index=False)
        #internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv", index=False)

        # 545,555 error sys1 exit
        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            config.app.debug,
            "population-restorator/output/balancer/territories.json",
            "population-restorator/output/balancer/houses.json",
        )

    async def divide(self, territory_id: int, prev_job: rq.job | None = None):
        # todo desc

        socdemo_client = SocDemoClient()

        men, women, indexes = await socdemo_client.get_population_pyramid(territory_id)

        distribution = "todo"

        if prev_job is None:
            houses_df = (await self.balance(territory_id))[1]

            return prdivide(houses_df,
                            distribution=distribution,
                            year=None,
                            verbose=config.app.debug
                            )

        return prdivide(*prev_job.result[1],
                        distribution=distribution,
                        year=None,
                        verbose=config.app.debug
                        )

    async def restore(self, territory_id: int):
        # todo
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesService()
