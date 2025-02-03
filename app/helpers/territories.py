"""
Internal functions for getting & parsing territories data from urban_api 
are defined here
"""

import json
import os
from dataclasses import dataclass

import pandas as pd

from app.utils import PopulationRestoratorApiConfig

from .requests import SuccessHandle, handle_request


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))


@dataclass
class BaseGetResult:
    """todo"""

    data: pd.DataFrame | None = None

    def is_success(self):
        pass


@dataclass
class SuccessGet(BaseGetResult):
    """todo"""

    def is_success(self):
        return True


@dataclass
class FailedToGet(BaseGetResult):
    """todo"""

    def is_success(self):
        return False


async def get_internal_territories(parent_id: int) -> pd.DataFrame:
    """
    Args: parent_id
    Returns: dataframe for all internal territories that contains territory with given parent_id

    index=territory_id
    territory_id (int): id of current territory
    name (str): name of current territory
    parent_id (int): territory on level above that has current territory as a child
    geometry (geojson) : coords of current territory

         territory_id                                name  parent_id  level                                           geometry
      3             3     Самойловское сельское поселение          2      4  {'type': 'Polygon', 'coordinates': [[[34.42168...
    ...          ...                                 ...        ...     ...                                                ...

    """

    # getting response
    url = f"{config.urban_api.host}{config.urban_api.base_path}/all_territories"

    params = {
        "parent_id": parent_id,
        "get_all_levels": "True",
    }

    headers = {
        "accept": "application/json",
    }

    result = await handle_request(url, params, headers)
    if not (isinstance(result, SuccessHandle)):
        return FailedToGet()
    data = result.response

    internal_territories_df = pd.DataFrame(data)

    # formatting

    columns = ["territory_id", "name", "parent_id", "level", "geometry"]
    formatted_territories_df = pd.DataFrame(columns=columns)
    formatted_territories_df.set_index("territory_id")

    for i in internal_territories_df["features"]:

        formatted_territories_df.loc[i["properties"]["territory_id"]] = {
            "name": i["properties"]["name"],
            "parent_id": i["properties"]["parent_id"],
            "level": i["properties"]["level"],
            "territory_id": i["properties"]["territory_id"],
            "geometry": i["geometry"],
        }

    return SuccessGet(formatted_territories_df)


async def get_population_for_child_territories(parent_id: int) -> pd.DataFrame:
    """
    Args: parent_id
    Returns: population dataframe with child territories with one level below and population of them for parent territory

      index=territory_id
      territory_id (int): id of current territory
      population (int) : amount of people in this territory

         territory_id  population
      5             5       20169
      6             6        1231
    ...           ...         ...

    """

    # getting response

    url = f"{config.urban_api.host}{config.urban_api.base_path}/territory/indicator_values"

    params = {
        "parent_id": parent_id,
        "indicators_ids": 1,
        "last_only": "true",
    }

    headers = {
        "accept": "application/json",
    }

    result = await handle_request(url, params, headers)
    if not (isinstance(result, SuccessHandle)):
        return FailedToGet()
    data = result.response

    population_df = pd.DataFrame(data)

    # formatting

    columns = ["territory_id", "population"]
    formatted_population_df = pd.DataFrame(columns=columns)
    formatted_population_df.set_index("territory_id")

    for i in population_df["features"]:

        formatted_population_df.loc[i["properties"]["territory_id"]] = {
            "territory_id": i["properties"]["territory_id"],
            "population": int(i["properties"]["indicators"][0]["value"]),
        }

    # print(formatted_population_df)
    return SuccessGet(formatted_population_df)


async def bind_population_to_territories(territories_df: pd.DataFrame) -> pd.DataFrame:
    """
    Args: territories dataframe

    Updates existing territories_df by adding population (int) column
    population_df is taken by parts for all parent_id's in func get_population_for_child_territories(id)

    Returns: new dataframe with additional column 'population' filled with int values
    """

    # save all unique parent_ids in dataframe
    parent_ids = set()
    for parent_id in territories_df["parent_id"]:
        parent_ids.add(parent_id)

    population_df = pd.DataFrame(columns=["territory_id", "population"])
    population_df.set_index("territory_id")

    # get population of child territories one level below for each parent territory and put it in df
    for parent_id in parent_ids:
        result = await get_population_for_child_territories(parent_id)

        if not (isinstance(result, SuccessGet)):
            return FailedToGet()

        temp_population_df = result.data
        population_df = pd.concat([population_df, temp_population_df])

    # merge dfs
    territories_df = territories_df.merge(population_df, on="territory_id", how="left")

    return SuccessGet(territories_df)
