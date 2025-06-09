"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import errno
import typing as tp
from datetime import date
from os import remove as os_remove
from pathlib import Path

import pandas as pd
import structlog
from population_restorator.forecaster import export_year_age_values
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability, SurvivabilityCoefficients

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide
from population_restorator.scenarios import forecast as prforecast

from app.http_clients import (
    SavingClient,
    SocDemoClient,
    UrbanClient,
)
from app.http_clients.common.exceptions import ObjectNotFoundError
from app.models import FertilityInterval, UrbanSocialDistribution
from app.utils.config import PopulationRestoratorConfig


class TerritoriesService:
    """
    This class implements interaction between UrbanClient, SocDemoClient
    with population_restorator library
    and saves forecasting data into postgresql database
    """

    def __init__(
        self,
        urban_client: UrbanClient,
        socdemo_client: SocDemoClient,
        saving_client: SavingClient,
        population_restorator_config: PopulationRestoratorConfig,
        debug: bool,
    ):

        self.urban_client = urban_client
        self.socdemo_client = socdemo_client
        self.saving_client = saving_client
        self.population_restorator_config = population_restorator_config
        self.debug = debug

    async def balance(self, territory_id: int, start_date: date | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        This method gathers necessary territories data from UrbanClient and starts balancing
        Args:
            territory_id: int, id of the territory which is going to be balanced
            start_date: date | None, the earliest date to be searched for, None for latest.
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

        internal_territories_df, internal_houses_df, population, main_territory = await asyncio.gather(
            self.urban_client.get_internal_territories(territory_id),
            self.urban_client.get_houses_from_territories(territory_id),
            self.urban_client.get_population_from_territory(territory_id, start_date),
            self.urban_client.get_territory(territory_id),
        )

        internal_territories_df = await self.urban_client.bind_population_to_territories(internal_territories_df)

        # internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv")
        # internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv")

        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            main_territory,
            self.debug,
        )

    async def divide(
        self, territory_id: int, houses_df: pd.DataFrame | None = None, start_date: date | None = None
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        This method uses balanced houses dataframe
        and runs population-restorator divide method
        which saves results into sqlite db

        Args:
            territory_id: int, id of the territory that is going to be divided
            houses_df: pd.DataFrame, balanced houses, optional argument for population_restorator divide input
                        if None then balance starts first, otherwise balance is skipped, used previous balance return
                id, house_id, territory_id, living_area, geometry, population
                10, 123438,   328,          963.81,      {...},    41
                ...
            start_date: date, the earliest date used to search information about, if None then used the latest

        Returns:
            houses_df: pd.DataFrame, todo
            distribution: pd.Series, todo
        """
        if houses_df is None:
            test_results = await self.balance(territory_id=territory_id, start_date=start_date)
            # test_results[0].to_csv(f"./territories{territory_id}.csv")
            # test_results[1].to_csv(f"./houses{territory_id}.csv")
            houses_df = test_results[1]

        year = start_date.year if start_date is not None else None

        oktmo_code: int = await self.urban_client.get_oktmo_of_territory_by_urban_db_id(territory_id)
        population_pyramid = await self.socdemo_client.get_population_pyramid(territory_id, oktmo_code, year)

        men_prob = [x / sum(population_pyramid.men) for x in population_pyramid.men]
        women_prob = [x / sum(population_pyramid.women) for x in population_pyramid.women]
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men_prob, women_prob)]
        distribution = SocialGroupsDistribution(primary, [])

        return prdivide(
            territory_id=territory_id,
            houses_df=houses_df,
            distribution=distribution,
            year=year,
            working_db_path=self.population_restorator_config.working_dirs.divide_working_db_path,
            verbose=self.debug,
        )

    async def get_forecasted_data(
        self,
        input_dir: str,
        territory_id: int,
        year_begin: int,
        years: int,
        scenario: tp.Literal["NEGATIVE", "NEUTRAL", "POSIVITE"],
    ) -> dict[str, list[UrbanSocialDistribution]]:
        """
        This method extracts from forecast output dbs
        Args:
            input_dir: str, path for directory which contains databases per year
            territory_id: int, id of the main territory which was
                          divided before and which data is going to be saved
            year_begin: int, first year to be saved
            years: int, for how many years saving is going to be
        """
        db_paths = [
            str(input_dir + f"year_{year}_terr_{territory_id}_scen_{scenario}.sqlite")
            for year in range(year_begin + 1, year_begin + years + 1)
        ]
        cur_year = year_begin + 1

        logger = structlog.get_logger()

        buildings_data: dict[str, list[UrbanSocialDistribution]] = {}

        for db_path in db_paths:
            logger.info(f"trying to get db data, db_path: {{{db_path}}}")
            if not (Path(db_path).exists()):
                logger.info(f"no such db {db_path}")
                continue
            year_data = export_year_age_values(db_path=db_path, territory_id=territory_id, verbose=self.debug)

            if year_data is None:
                logger.error(f"got no data from, db_path: {{{db_path}}}")
                raise ObjectNotFoundError()

            buildings_year_data: list[UrbanSocialDistribution] = []
            for index, values in year_data.iterrows():
                buildings_year_data.append(
                    UrbanSocialDistribution(
                        building_id=values["house_id"],
                        scenario=scenario,
                        year=cur_year,
                        sex="MALE",
                        age=values["age"],
                        value=values["men"],
                    )
                )
                buildings_year_data.append(
                    UrbanSocialDistribution(
                        building_id=values["house_id"],
                        scenario=scenario,
                        year=cur_year,
                        sex="FEMALE",
                        age=values["age"],
                        value=values["women"],
                    )
                )
            cur_year += 1

            buildings_data[db_path] = buildings_year_data

        return buildings_data

    async def delete_previous_forecasted_data(
        self,
        input_dir: str,
        territory_id: int,
        year_begin: int,
        years: int,
        scenario: tp.Literal["NEGATIVE", "NEUTRAL", "POSIVITE"],
    ):
        """
        This method extracts from forecast output dbs and deletes it from saving api
        Args:
            input_dir: str, path for directory which contains databases per year
            territory_id: int, id of the main territory which was
                          divided before and which data is going was saved
            year_begin: int, first year was saved
            years: int, for how many years saving was
        """

        buildings_data = await self.get_forecasted_data(input_dir, territory_id, year_begin, years, scenario)

        logger = structlog.getLogger()
        for db_path, values in buildings_data.items():
            logger.info(f"deleting previous forecasted data, db_path: {{ {db_path} }}")
            await self.saving_client.delete_forecasted_data(values)

            try:
                os_remove(db_path)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    async def insert_forecasted_data(
        self,
        input_dir: str,
        territory_id: int,
        year_begin: int,
        years: int,
        scenario: tp.Literal["NEGATIVE", "NEUTRAL", "POSIVITE"],
    ):
        """
        This method extracts from forecast output dbs and posts it to saving api
        Args:
            input_dir: str, path for directory which contains databases per year
            territory_id: int, id of the main territory which was
                          divided before and which data is going to be saved
            year_begin: int, first year to be saved
            years: int, for how many years saving is going to be
        """

        buildings_data = await self.get_forecasted_data(input_dir, territory_id, year_begin, years, scenario)

        logger = structlog.getLogger()
        for db_path, values in buildings_data.items():
            logger.info(f"saving forecasted data, db_path: {{ {db_path} }}")

            await self.saving_client.post_forecasted_data(values)

    async def restore(
        self,
        territory_id: int,
        year_begin: int,
        years: int,
        scenario: tp.Literal["NEGATIVE", "NEUTRAL", "POSIVITE"],
        from_scratch: bool,
    ) -> tp.NoReturn:
        """
        Lasciate ogne speranza, voi ch’entrate

        This method is used for forecasting N years population for given territory
        Args:
            territory_id: int, id of the territory which is going to be forecasted
            year_begin: int, divided data for this year is used to start forecasting
            years: int, amount of years to be forecasted
                if year_begin is 2025 and years is 2, forecasting for 2026 and 2027
            scenario: Literal, affects the birthrate stats
            from_scratch: bool, if true dividing first, otherwise using dividing data from divide output db
        """

        oktmo_code = await self.urban_client.get_oktmo_of_territory_by_urban_db_id(territory_id)
        coeffs = await self.socdemo_client.get_surviability_coeffs_from_last_pyramids(
            territory_id, oktmo_code, year_begin
        )

        fertility_interval = FertilityInterval(**self.population_restorator_config.fertility_interval.model_dump())
        birth_stats = await self.socdemo_client.get_birth_stats(
            territory_id, fertility_interval, oktmo_code=oktmo_code, year=year_begin
        )
        birth_stats.adapt_to_scenario(scenario)

        if from_scratch:
            await self.divide(territory_id, start_date=date(year_begin, 1, 1))

        await self.delete_previous_forecasted_data(
            self.population_restorator_config.working_dirs.forecast_working_dir_path,
            territory_id=territory_id,
            year_begin=year_begin,
            years=years,
            scenario=scenario,
        )

        prforecast(
            houses_db=self.population_restorator_config.working_dirs.divide_working_db_path,
            territory_id=territory_id,
            coeffs=coeffs,
            year_begin=year_begin,
            years=years,
            boys_to_girls=birth_stats.boys_to_girls,
            fertility_coefficient=birth_stats.fertility_coefficient,
            fertility_begin=birth_stats.fertility_interval.start,
            fertility_end=birth_stats.fertility_interval.end,
            scenario=scenario,
            verbose=self.debug,
            working_dir=self.population_restorator_config.working_dirs.forecast_working_dir_path,
        )

        await self.insert_forecasted_data(
            input_dir=self.population_restorator_config.working_dirs.forecast_working_dir_path,
            territory_id=territory_id,
            year_begin=year_begin,
            years=years,
            scenario=scenario,
        )
