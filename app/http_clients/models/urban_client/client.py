"""
This class is used for taking data from foreign api
with information about population, houses & territories
"""

from __future__ import annotations

import asyncio
import os
from asyncio import Semaphore
from datetime import date
from typing import Any

import pandas as pd
import structlog

from app.http_clients.common import (
    BaseClient,
    ObjectNotFoundError,
    handle_exceptions,
    handle_get_request,
)
from app.utils import PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()


class UrbanClient(BaseClient):
    """Urban API client that uses HTTP/HTTPS as transport."""

    def __post_init__(self):
        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

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
            "get_all_levels": "true",
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

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
    async def get_oktmo_of_territory_by_urban_db_id(self, territory_id: int) -> int | None:
        """
        Args: territory_id (int)
        Returns: oktmo code (int)
        """

        # getting response
        url = f"{self.config.host}/api/v1/territories/{territory_id}"

        params = {"territories_ids": territory_id, "centers_only": "true"}

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()
        if data["features"][0]["properties"]["oktmo_code"] is not None:
            return int(data["features"][0]["properties"]["oktmo_code"])
        else:
            return None

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
        oktmo (int): oktmo territory's code

             territory_id                                name  parent_id  level                                           geometry  oktmo
          3             3     Самойловское сельское поселение          2      4  {'type': 'Polygon', 'coordinates': [[[34.42168...  43400
        ...          ...                                 ...        ...     ...                                                ...    ...

        """

        # getting response
        url = f"{self.config.host}/api/v1/territories/{territory_id}"

        params = {"territories_ids": territory_id, "centers_only": "true"}

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        data = data["features"][0]

        # formatting
        territory_df = pd.DataFrame(columns=["territory_id", "name", "parent_id", "level", "geometry", "oktmo"])
        territory_df.set_index("territory_id")

        territory_df.loc[territory_id] = {
            "territory_id": territory_id,
            "name": data["properties"]["name"],
            "parent_id": data["properties"]["parent"]["id"],
            "level": data["properties"]["level"],
            "geometry": data["geometry"],
            "oktmo": data["properties"]["oktmo_code"],
        }

        return territory_df

    @handle_exceptions
    async def get_population_for_child_territories(self, parent_id: int, last_only: bool = True) -> pd.DataFrame:
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
        # todo add time
        params = {
            "parent_id": parent_id,
            "indicator_ids": self.config.const_request_params["population_indicator"],
            "last_only": "true" if last_only else "false",
            "value_type": self.config.const_request_params["population_value_type_indicator"],
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

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

        semaphore = Semaphore(5)

        async def fetch_with_semaphore(parent_id):
            async with semaphore:
                return await self.get_population_for_child_territories(parent_id)

        # get population of child territories one level below for each parent territory and put it in df
        tasks = [fetch_with_semaphore(parent_id) for parent_id in parent_ids]

        results = await asyncio.gather(*tasks)
        population_dfs = [df for df in results if df is not None]
        if len(population_dfs) != 0:
            population_df = pd.concat(population_dfs)

        # merge dfs
        return pd.merge(territories_df, population_df, on="territory_id", how="left")

    async def get_houses_from_territories(self, territory_parent_id: int) -> pd.DataFrame:
        """
        Args: parent_id (int)
        Returns: dataframe with all internal houses inside this territory and child territories

        index=house_id
        house_id (int): id of current house
        territory_id (int): id of territory which contains current house
        geometry (geojson) : coords of current territory

        /todo table example here/
        ...          ...                                 ...        ...     ...                                                ...

        """

        # getting response

        url = f"{self.config.host}/api/v1/territory/{territory_parent_id}/physical_objects_geojson"

        params = {
            "territory_id": territory_parent_id,
            "include_child_territories": "true",
            "cities_only": "true",
            "physical_object_type_id": self.config.const_request_params["house_type"],
            "centers_only": "true",  # ???
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        internal_houses_df = pd.DataFrame(data)

        # formatting
        columns = ["house_id", "territory_id", "living_area"]
        formatted_houses_df = pd.DataFrame(columns=columns)
        formatted_houses_df.set_index("house_id", drop=False, inplace=True)

        for i in internal_houses_df["features"]:
            try:
                living_area_modeled = i["properties"]["building"]["properties"]["living_area_modeled"]
                living_area_official = i["properties"]["building"]["properties"]["living_area_official"]
            except KeyError as exc:
                logger.error(f"house with id {i['properties']['building']['id']} has no living_area property")
                logger.error(exc, i)
                continue
            except TypeError as exc:
                logger.error(
                    f"something wrong with house properties territory_parent_id: {territory_parent_id} house_id: {i['properties']['territories'][0]['id']}"
                )
                logger.error(exc, i)
                continue
            formatted_houses_df.loc[i["properties"]["building"]["id"]] = {
                "house_id": i["properties"]["building"]["id"],
                "territory_id": i["properties"]["territories"][0]["id"],
                # prefering living_area_modeled than living_are_official, if none of this available -> 0
                "living_area": living_area_modeled if living_area_modeled is not None else (living_area_official or 0),
            }

        return formatted_houses_df

    @handle_exceptions
    async def get_population_from_territory(self, territory_id: int, start_date: date | None = None) -> int:
        """
        Args:
            territory_id (int): id of given territory
            start_date (date): earliest date to be searched for, None for the latest
        Returns: amount of people on this territory
        """
        # getting response
        url = f"{self.config.host}/api/v1/territory/{territory_id}/indicator_values"

        params = {
            "territory_id": territory_id,
            "indicator_ids": self.config.const_request_params["population_indicator"],
            "last_only": "true" if start_date is None else "false",
            "value_type": self.config.const_request_params["population_value_type_indicator"],
            "include_child_territories": "false",
            "cities_only": "false",
        }

        if start_date is not None:
            params["start_date"] = (str(start_date),)

        headers = {
            "accept": "application/json",
        }

        data = await handle_get_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        if start_date is None:
            return int(data[0]["value"])

        indicator_value_saved: dict[str, Any] = None
        start_date = str(start_date)
        for indicator_value in data:
            if (
                indicator_value["date_value"] >= start_date
                and indicator_value_saved is None
                or (
                    indicator_value["date_value"] >= start_date
                    and indicator_value_saved is None
                    and indicator_value["date_value"] < indicator_value_saved
                )
            ):
                indicator_value_saved = indicator_value

        # formatting
        return int(indicator_value_saved["value"])
