# todo desc

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

        # tobeaddedtrycatch i guess

        internal_territories_df = await urban_client.get_internal_territories(territory_id)

        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)

        internal_houses_df = await urban_client.get_houses_from_territories(territory_id)

        # result = prbalance(100000, internal_territories_df, internal_houses_df)

        # tobechanged
        return True

    async def divide(self, territory_id: int):
        # todo
        pass

    async def restore(self, territory_id: int):
        # todo
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesService()
