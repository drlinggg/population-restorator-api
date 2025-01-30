# todo desc

import pandas as pd

# torename
from population_restorator.scenarios import balance as prbalance

from app.helpers import (
    bind_population_to_territories,
    get_internal_territories,
    get_population_for_child_territories,
)


class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int):
        """ """
        internal_territories_df = await get_internal_territories(territory_id)
        internal_territories_df = await bind_population_to_territories(internal_territories_df)
        # todo add houses getter
        # id living_area territory_id geometry

        # start lib
        #result = prbalance(100000, internal_territories_df, pd.DataFrame())

    async def divide(self, territory_id: int):
        # todo
        pass

    async def restore(self, territory_id: int):
        # todo
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesService()
