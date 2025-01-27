# todo desc

import pandas as pd

import itertools

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

from population_restorator.utils.data_saver import (
    to_file,
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

        # get houses someday
                #id living_area inner_territory geometry

        #for test
        houses_df = read_file("houses.geojson")

        inner_territories_df, outer_territories_df = (
            await pretty_format(
                inner_territories_df, outer_territories_df
            )
        )
        
        
        # start lib
        # idk why it crushes because of zero division i guess if there no home in outer_territory
        city = city_as_territory(100000, outer_territories_df, inner_territories_df, houses_df)
        
        #for i in range(len(city.inner_territories)):
        #    territory = city.inner_territories[i]
        #    distribution = [it.get_total_living_area() for it in territory.inner_territories]
        #    total_living_area = sum(distribution)
        #    if (total_living_area == 0):
        #        print(territory.inner_territories[0])
        #
        #distribution = [area / total_living_area for area in distribution]

        balance_territories(city)
        balance_houses(city)
    
        #todo remove it to somewhere else
        outer_territories_output = 'outer.csv'
        inner_territories_output = 'inner.csv'
        output = 'house.geojson'
        
        outer_territories_new_df = pd.DataFrame(
            (
                {
                    "name": ot.name,
                    "population": ot.population,
                    "inner_territories_population": ot.get_total_territories_population(),
                    "houses_number": ot.get_all_houses().shape[0],
                    "houses_population": ot.get_total_houses_population(),
                    "total_living_area": ot.get_total_living_area(),
                }
                for ot in city.inner_territories
            )
        )
        to_file(outer_territories_new_df, outer_territories_output)

        inner_territories_new_df = pd.DataFrame(
            itertools.chain.from_iterable(
                (
                    {
                        "name": it.name,
                        "population": it.population,
                        "inner_territories_population": it.get_total_territories_population(),
                        "houses_number": it.get_all_houses().shape[0],
                        "houses_population": it.get_total_houses_population(),
                        "total_living_area": it.get_total_living_area(),
                    }
                    for it in ot.inner_territories
                )
                for ot in city.inner_territories
            )
        )
        to_file(inner_territories_new_df, inner_territories_output)

        to_file(city.get_all_houses(), output)

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
