import abc
import asyncio
import json
import os
from dataclasses import dataclass
from functools import wraps
from typing import Callable

import pandas as pd
import structlog
from aiohttp import ClientConnectionError, ClientSession, ClientTimeout

from app.http_clients.common import (
    APIConnectionError,
    APITimeoutError,
    BaseClient,
    ObjectNotFoundError,
    handle_request,
)
from app.utils import PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()


def _handle_exceptions(func: Callable) -> Callable:
    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientConnectionError as exc:
            logger.error(f"failed to send request, status {exc}")
            raise APIConnectionError("Error on connection to Urban API") from exc
        except asyncio.exceptions.TimeoutError as exc:
            logger.error(f"failed to connect to {url}: {exc}")
            raise APITimeoutError("Timeout expired on Urban API request") from exc

    return _wrapper


class UrbanClient(BaseClient):
    """Urban API client that uses HTTP/HTTPS as transport."""

    def __init__(self):
        self.config: ApiConfig | None = config.urban_api

        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    async def is_alive(self) -> bool:
        """Check if Urban API instance is responding."""
        # todo
        return True

    @_handle_exceptions
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
        url = f"{self.config.host}{self.config.base_path}/all_territories"

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
        formatted_territories_df.set_index("territory_id")

        for i in internal_territories_df["features"]:
            formatted_territories_df.loc[i["properties"]["territory_id"]] = {
                "name": i["properties"]["name"],
                "parent_id": i["properties"]["parent"]["id"],
                "level": i["properties"]["level"],
                "territory_id": i["properties"]["territory_id"],
                "geometry": i["geometry"],
            }

        return formatted_territories_df

    @_handle_exceptions
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

        url = f"{self.config.host}{self.config.base_path}/territory/indicator_values"

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

    @_handle_exceptions
    async def bind_population_to_territories(self, territories_df: pd.DataFrame) -> pd.DataFrame:
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
            temp_population_df = await self.get_population_for_child_territories(parent_id)

            if temp_population_df is None:
                raise ObjectNotFoundError()
            population_df = pd.concat([population_df, temp_population_df])

        # merge dfs
        territories_df = territories_df.merge(population_df, on="territory_id", how="left")

        return territories_df

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
        url = f"{self.config.host}{self.config.base_path}/territory/{territory_parent_id}/physical_objects_geojson"

        params = {
            "territory_id": territory_parent_id,
            "include_child_territories": "true",
            "cities_only": "true",
            "physical_object_type_id": "4",
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
        formatted_houses_df.set_index("house_id")

        print(internal_houses_df["features"][0]["properties"]["building"])

        for i in internal_houses_df["features"]:
            formatted_houses_df.loc[i["properties"]["building"]["id"]] = {
                # "name": i["properties"]["name"],
                "house_id": i["properties"]["building"]["id"],
                "territory_id": i["properties"]["territories"][0]["id"],
                "living_area": i["properties"]["building"]["properties"]["living_area_official"],
                "geometry": i["geometry"],
            }

        return formatted_houses_df

    @_handle_exceptions
    async def get_population_from_territory(self, territory_id: int, last_only=True) -> int:
        """
        Args: territory_id (int): id of given territory
        Returns: amount of people on this territory
        """
        # getting response

        indicator_id_for_population = 1
        value_type = "real"

        url = f"{self.config.host}{self.config.base_path}/territory/{territory_id}/indicator_values"

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
