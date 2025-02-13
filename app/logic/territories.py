# todo desc

import pandas as pd

# torename
from population_restorator.scenarios import balance as prbalance

from app.helpers import (
    SuccessGet,
    bind_population_to_territories,
    get_internal_territories,
    get_population_for_child_territories,
    get_houses_from_territories,
)


class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int):
        """ """
        result = await get_internal_territories(territory_id)

        # tobechanged
        if not (isinstance(result, SuccessGet)):
            return False
        internal_territories_df = result.data

        result = await bind_population_to_territories(internal_territories_df)

        # tobechanged
        if not (isinstance(result, SuccessGet)):
            return False
        internal_territories_df = result.data

        result = await get_houses_from_territories(territory_id)

        # tobechanged
        #if not (isinstance(result, SuccessGet)):
        #    return False
        internal_houses_df = result.data

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
