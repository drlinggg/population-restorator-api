# todo desc
from __future__ import annotations

import pandas as pd

# torename
from population_restorator.scenarios import balance as prbalance

from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)


class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int):
        """ """

        urban_client = UrbanClient()

        internal_territories_df = await urban_client.get_internal_territories(territory_id)
        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)
        internal_houses_df = await urban_client.get_houses_from_territories(territory_id)
        population = await urban_client.get_population_from_territory(territory_id)

        # internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv", index=False)
        # internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv", index=False)

        result = prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            1,
            "population-restorator/output/territories.json",
            "population-restorator/output/houses.json",
        )

    async def divide(self, territory_id: int):
        # todo
        pass

    async def restore(self, territory_id: int):
        # todo
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesService()
