"""
Internal functions for getting & parsing houses data from urban_api 
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



async def get_houses_from_territories(territory_parent_id: int) -> pd.DataFrame:
    """
    Args: parent_id (int)
    Returns: dataframe with all internal houses inside this territory and child territories

    index=/todo/
    house_id (int): id of current house
    todo mb add name (str)
    territory_id (int): id of territory which contains current house
    living_area (float): 
    geometry (geojson) : coords of current territory

    /todo table example here/
    ...          ...                                 ...        ...     ...                                                ...

    """

    # getting response
    url = f"{config.urban_api.host}{config.urban_api.base_path}/territory/{territory_parent_id}/physical_objects_geojson"

    params = {
        "territory_id": territory_parent_id,
        "include_child_territories": "true",
        "cities_only": "true",
        "physical_object_type_id": '4',
    }

    headers = {
        "accept": "application/json",
    }

    result = await handle_request(url, params, headers)
    if not (isinstance(result, SuccessHandle)):
        return FailedToGet()

    data = result.response
    internal_houses_df = pd.DataFrame(data)

    # formatting
    columns = ["house_id", "territory_id", "living_area", "geometry"]
    formatted_houses_df = pd.DataFrame(columns=columns)
    formatted_houses_df.set_index("house_id")

    for i in internal_houses_df['features']:

        formatted_houses_df.loc[i["properties"]['living_building']['id']] = {
            #"name": i["properties"]["name"],
            "house_id": i["properties"]["living_building"]["id"],
            "territory_id": i["properties"]["territories"][0]['id'],
            "living_area": i["properties"]["living_building"]["living_area"],
            "geometry": i["geometry"],
        }

    return SuccessGet(formatted_houses_df)

