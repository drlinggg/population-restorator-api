# todo desc

import pandas as pd

from app.helpers import (
    bind_inners_to_outers,
    bind_population_to_territories,
    get_internal_territories,
    get_territory_level,
    save_first_two_layers_of_internal_territories,
    pretty_format,
)

from population_restorator.balancer import (
    balance_territories,
    balance_houses,
)

from population_restorator.utils.data_structure import (
    city_as_territory,
)

#tobedeleted
from population_restorator.utils.data_loader import (
    read_file,
)


class TerritoriesService:
    # todo desc

    async def balance(self, territory_id: int):
        # todo
        # debug f balance {id}
        print(f"balance {territory_id}")

        internal_territories_df = await get_internal_territories(territory_id)

        parent_territory_lvl = await get_territory_level(territory_id)

        outer_territories_df, inner_territories_df = (
            await save_first_two_layers_of_internal_territories(
                internal_territories_df, parent_territory_lvl
            )
        )

        inner_territories_df, outer_territories_df = (
            await bind_inners_to_outers(
                inner_territories_df, outer_territories_df
            )
        )

        inner_territories_df, outer_territories_df = (
            await bind_population_to_territories(
                inner_territories_df, outer_territories_df, territory_id
            )
        )

        # get houses
                #id living_area inner_territory geometry

        # id name population (outer) geometry
        inner_territories_df, outer_territories_df = (
            await pretty_format(
                inner_territories_df, outer_territories_df
            )
        )
        
        #test
        houses_df = read_file("houses.geojson")
        print(inner_territories_df)
        
        # start lib
        city = city_as_territory(500, outer_territories_df, inner_territories_df, houses_df)
        balance_territories(city)
        balance_houses(city)

        pass

    async def divide(self, territory_id: int):
        # todo
        print(f"divide {territory_id}")
        pass

    async def restore(self, territory_id: int):
        # todo
        print(f"restore {territory_id}")
        pass


def get_territories_service() -> TerritoriesService:
    return TerritoriesService()
