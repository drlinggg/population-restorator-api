"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import os

import pandas as pd
import sqlalchemy
import structlog
import typing as tp
from population_restorator.forecaster import export_year_age_values
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability, SurvivabilityCoefficients

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide
from population_restorator.scenarios import forecast as prforecast

from app.db import MetaData, PostgresConnectionManager
from app.db.entities import ScenarioEnum, SexEnum, t_forecasted
from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)
from app.http_clients.common.exceptions import ObjectNotFoundError
from app.utils import DBConfig, PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))


# add this to middleware and _postgres_conn
class TerritoriesService:
    """
    This class implements interaction between UrbanClient, SocDemoClient
    with population_restorator library 
    and saves forecasting data into postgresql database
    """

    def __init__(self, dbconfig: DBConfig):
        self.db_config = dbconfig
        self.connection_manager: PostgresConnectionManager | None = None

    async def get_connect(self) -> None:
        self.connection_manager = PostgresConnectionManager(self.db_config, structlog.get_logger())
        await self.connection_manager.refresh()

    async def shut_connect(self) -> None:
        if self.connection_manager is not None:
            await self.connection_manager.shutdown()

    async def balance(self, territory_id: int) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        This method gathers necessary territories data from UrbanClient and starts balancing
        Args:
            territory_id: int, id of the territory which is going to be balanced
        Returns:
            territories_df: pd.DataFrame, balanced territories
                id, name, population, inner_territories_population, houses_number, houses_population, total_living_area
                2,  name, 15716,      15716,                        93,            15716,             277254
                ...

            houses_df: pd.DataFrame, balanced houses
                id, house_id, territory_id, living_area, geometry, population
                10, 123438,   328,          963.81,      {...},    41
                ...
        """

        urban_client = UrbanClient()

        internal_territories_df = await urban_client.get_internal_territories(territory_id)
        internal_territories_df = await urban_client.bind_population_to_territories(internal_territories_df)

        internal_houses_df, population, main_territory = await asyncio.gather(
            urban_client.get_houses_from_territories(territory_id),
            urban_client.get_population_from_territory(territory_id),
            urban_client.get_territory(territory_id),
        )

        # internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv")
        # internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv")

        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            main_territory,
            config.app.debug,
        )

    async def divide(self, territory_id: int, houses_df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.Series]:
        """
        This method uses balanced houses dataframe
        and runs population_restorator divide method 
        which saves results into sqlite db

        Args:
            territory_id: int, id of the territory that is going to be divided
            houses_df: pd.DataFrame, balanced houses, optional argument for population_restorator divide input
                        if None then balance starts first, otherwise balance is skipped, used previous balance return
                id, house_id, territory_id, living_area, geometry, population
                10, 123438,   328,          963.81,      {...},    41
                ...

        Returns:
            houses_df: pd.DataFrame, todo
            distribution: pd.Series, todo
        """

        socdemo_client = SocDemoClient()

        men, women, indexes = await socdemo_client.get_population_pyramid(territory_id)

        men = [x / sum(men) for x in men]
        women = [x / sum(women) for x in women]

        # todo add working indexes and solve 70-75 problem
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men, women)]
        distribution = SocialGroupsDistribution(primary, [])

        if houses_df is None:
            houses_df = (await self.balance(territory_id))[1]

        return prdivide(
            territory_id=territory_id,
            houses_df=houses_df,
            distribution=distribution,
            year=None,
            verbose=config.app.debug,
        )

    async def insert_forecasted_data(
        self,
        input_dir: str,
        territory_id: int,
        year_begin: int,
        years: int
    ) -> tp.NoReturn:
        """
        This method extracts from forecast output dbs and inserts it in postgres database
        Args:
            input_dir: str, path for directory which contains databases per year
            territory_id: int, id of the main territory which was been
                          divided before and which data is going to be saved
            year_begin: int, first year to be saved
            years: int, for how many years saving is going to be
        """
        db_paths = [f"{input_dir}/year_{year}.sqlite" for year in range(year_begin + 1, year_begin + years + 1)]
        cur_year = year_begin + 1

        logger = structlog.get_logger()

        await self.get_connect()
        async with self.connection_manager.get_connection() as conn:

            for db_path in db_paths:
                year_data = export_year_age_values(
                    db_path=db_path,
                    territory_id=territory_id,
                    verbose=config.app.debug
                )

                logger.info(f"uploading {db_path} into forecasted table")
                if year_data is None:
                    logger.error(f"got no data from {db_path}")
                    raise ObjectNotFoundError()

                data_to_insert = []
                for index, values in year_data.iterrows():
                    data_to_insert.append(
                        {
                            "building_id": values["house_id"],
                            "scenario": ScenarioEnum.NEUTRAL,
                            "year": cur_year,
                            "sex": SexEnum.MALE,
                            "age": values["age"],
                            "value": values["men"],
                        }
                    )
                    data_to_insert.append(
                        {
                            "building_id": values["house_id"],
                            "scenario": ScenarioEnum.NEUTRAL,
                            "year": cur_year,
                            "sex": SexEnum.FEMALE,
                            "age": values["age"],
                            "value": values["women"],
                        }
                    )

                if data_to_insert:
                    stmt = sqlalchemy.insert(t_forecasted)
                    await conn.execute(stmt, data_to_insert)

                cur_year += 1
                await conn.commit()

        await self.shut_connect()

    async def restore(
        self,
        territory_id: int,
        survivability_coefficients: dict[str, tuple[float]],
        year_begin: int,
        years: int,
        boys_to_girls: float,
        fertility_coefficient: float,
        fertility_begin: int,
        fertility_end: int,
        from_scratch: bool,
    ) -> tp.NoReturn:
        """
        Lasciate ogne speranza, voi ch’entrate
        This method is used for forecasting N years population for given territory
        Args:
            territory_id: int, id of the territory which is going to be forecasted
            survivability_coefficients: dict[str, tuple[float]], used to predict population changing through years
                dict['men'] = (0.99, 0.99, 0.98, 0.95, 0.97, ...)
                dict['women'] = (0.99, 0.99, 0.98, 0.95, 0.97, ...)
                tuple[x] is change to survive for x years old male/female
            year_begin: int, divided data for this year is used to start forecasting
            years: int, amount of years to be forecasted
                if year_begin is 2025 and years is 2, forecasting for 2026 and 2027
            fertility_coefficient: float, births per woman value
            fertility_begin & fertility_end: int, age of beginning and stopping to giving birth
            from_scratch: bool, if true dividing first, otherwise using dividing data from divide output db
        """


        # example
        coeffs = SurvivabilityCoefficients(
            [1 / (i * 0.1) for i in range(1, 100)], [1 / (i * 0.1) for i in range(1, 100)]
        )

        if from_scratch:
            await self.divide(territory_id)

        prforecast(
            houses_db="/home/banakh/work/population-restorator-api/population-restorator/test.db",  # toberenamed
            territory_id=territory_id,
            coeffs=coeffs,  # should be replaced to survivability_coefficients
            year_begin=year_begin,
            years=years,
            boys_to_girls=boys_to_girls,
            fertility_coefficient=fertility_coefficient,
            fertility_begin=fertility_begin,
            fertility_end=fertility_end,
            verbose=config.app.debug,
        )

        forecast_output_dir = "/home/banakh/shitstorage"

        await self.insert_forecasted_data(
            input_dir=forecast_output_dir,
            territory_id=territory_id,
            year_begin=year_begin,
            years=years
        )
