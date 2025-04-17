"""
This class is used for taking data from foreign api
with information about population, houses & territories
"""

from __future__ import annotations

import os

import pandas as pd
import structlog

from app.http_clients.common import (
    BaseClient,
    ObjectNotFoundError,
    handle_exceptions,
    handle_request,
)
from app.utils import ApiConfig, PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()


class UrbanClient(BaseClient):
    """Urban API client that uses HTTP/HTTPS as transport."""

    def __init__(self):
        self.config: ApiConfig | None = config.urban_api

        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    async def is_alive(self) -> bool:

        url = f"{self.config.host}/api/v1/health_check/ping"

        result = handle_request(url)

        if result:
            return True

        return False

    def __str__(self):
        return "UrbanClient"

    @handle_exceptions
    async def get_internal_territories(self, parent_id: int) -> pd.DataFrame:
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
        url = f"{self.config.host}/api/v1/all_territories"

        params = {
            "parent_id": parent_id,
            "get_all_levels": "True",
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        internal_territories_df = pd.DataFrame(data)

        # formatting
        columns = ["territory_id", "name", "parent_id", "level", "geometry"]
        formatted_territories_df = pd.DataFrame(columns=columns)
        formatted_territories_df.set_index("territory_id", inplace=True)

        for i in internal_territories_df["features"]:
            formatted_territories_df.loc[i["properties"]["territory_id"]] = {
                "name": i["properties"]["name"],
                "parent_id": i["properties"]["parent"]["id"],
                "level": i["properties"]["level"],
                "territory_id": i["properties"]["territory_id"],
                "geometry": i["geometry"],
            }

        return formatted_territories_df

    @handle_exceptions
    async def get_territory(self, territory_id: int) -> pd.DataFrame:
        """
        Args: territory_id
        Returns: dataframe for with 1 element, this territory info

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
        url = f"{self.config.host}/api/v1/territories/{territory_id}"

        params = {
            "territories_ids": territory_id,
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        data = data["features"][0]

        # formatting
        territory_df = pd.DataFrame(columns=["territory_id", "name", "parent_id", "level", "geometry"])
        territory_df.set_index("territory_id")

        territory_df.loc[territory_id] = {
            "territory_id": territory_id,
            "name": data["properties"]["name"],
            "parent_id": data["properties"]["parent"]["id"],
            "level": data["properties"]["level"],
            "geometry": data["geometry"],
        }

        return territory_df

    @handle_exceptions
    async def get_population_for_child_territories(self, parent_id: int) -> pd.DataFrame:
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

        url = f"{self.config.host}/api/v1/territory/indicator_values"

        params = {
            "parent_id": parent_id,
            "indicators_ids": 1,
            "last_only": "true",
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

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

        return formatted_population_df

    @handle_exceptions
    async def bind_population_to_territories(self, territories_df: pd.DataFrame) -> pd.DataFrame:
        """
        Args: territories dataframe

        Updates existing territories_df by adding population (int) column
        population_df is taken by parts for all parent_id's in func get_population_for_child_territories(id)

        Returns: new dataframe with additional column 'population' filled with int values
        """

        # save all unique parent_ids in dataframe
        parent_ids = set(territories_df["parent_id"])

        population_df = pd.DataFrame(columns=["territory_id", "population"])
        population_df.set_index("territory_id")

        # get population of child territories one level below for each parent territory and put it in df
        for parent_id in parent_ids:
            temp_population_df = await self.get_population_for_child_territories(parent_id)

            if temp_population_df is None:
                raise ObjectNotFoundError()
            population_df = pd.concat([population_df, temp_population_df])

        # merge dfs

        return pd.merge(territories_df, population_df, on="territory_id", how="left")

    async def get_houses_from_territories(self, territory_parent_id: int) -> pd.DataFrame:
        """
        Args: parent_id (int)
        Returns: dataframe with all internal houses inside this territory and child territories

        index=house_id
        house_id (int): id of current house
        todo mb add name (str)
        territory_id (int): id of territory which contains current house
        living_area (float):
        geometry (geojson) : coords of current territory

        /todo table example here/
        ...          ...                                 ...        ...     ...                                                ...

        """

        # getting response

        house_type = "4"

        url = f"{self.config.host}/api/v1/territory/{territory_parent_id}/physical_objects_geojson"

        params = {
            "territory_id": territory_parent_id,
            "include_child_territories": "true",
            "cities_only": "true",
            "physical_object_type_id": house_type,
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        internal_houses_df = pd.DataFrame(data)

        # formatting
        columns = ["house_id", "territory_id", "living_area", "geometry"]
        formatted_houses_df = pd.DataFrame(columns=columns)
        formatted_houses_df.set_index("house_id", drop=False, inplace=True)

        for i in internal_houses_df["features"]:

            living_area_modeled = i["properties"]["building"]["properties"]["living_area_modeled"]
            living_area_official = i["properties"]["building"]["properties"]["living_area_official"]

            formatted_houses_df.loc[i["properties"]["building"]["id"]] = {
                # "name": i["properties"]["name"],
                "house_id": i["properties"]["building"]["id"],
                "territory_id": i["properties"]["territories"][0]["id"],
                # prefering living_area_modeled than living_are_official, if none of this available -> 0
                "living_area": living_area_modeled if living_area_modeled is not None else (living_area_official or 0),
                "geometry": i["geometry"],
            }

        return formatted_houses_df

    @handle_exceptions
    async def get_population_from_territory(self, territory_id: int, last_only: bool = True) -> int:
        """
        Args: territory_id (int): id of given territory
        Returns: amount of people on this territory
        """
        # getting response

        indicator_id_for_population = 1
        value_type = "real"

        url = f"{self.config.host}/api/v1/territory/{territory_id}/indicator_values"

        params = {
            "territory_id": territory_id,
            "indicator_ids": indicator_id_for_population,
            "last_only": f"{last_only}",
            "value_type": value_type,
            "include_child_territories": "false",
            "cities_only": "false",
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        # formatting
        population = data[0]["value"]
        return int(population)
