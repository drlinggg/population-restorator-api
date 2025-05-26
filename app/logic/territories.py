"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import typing as tp
from datetime import date

import pandas as pd
import structlog
from population_restorator.forecaster import export_year_age_values
from population_restorator.models import (
    SocialGroupsDistribution,
    SocialGroupWithProbability,
    SurvivabilityCoefficients
)
from app.schemas import UrbanSocialDistributionPost
from app.http_clients.common.exceptions import ObjectNotFoundError
from app.models import UrbanSocialDistribution, FertilityPerWoman

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide
from population_restorator.scenarios import forecast as prforecast

from app.http_clients import (
    SocDemoClient,
    UrbanClient,
    SavingClient,
)


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
        debug: bool,
        forecast_working_dir_path: str,
        divide_working_db_path: str,
    ):

        self.urban_client = urban_client
        self.socdemo_client = socdemo_client
        self.saving_client = saving_client
        self.debug = debug
        self.forecast_working_dir_path = forecast_working_dir_path
        self.divide_working_db_path = divide_working_db_path

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

    async def divide(self, territory_id: int, houses_df: pd.DataFrame | None = None, start_date: date | None = None) -> tuple[pd.DataFrame, pd.Series]:
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
            houses_df = (await self.balance(territory_id=territory_id, start_date=start_date))[1]

        oktmo_code: int = await self.urban_client.get_oktmo_of_territory_by_urban_db_id(territory_id)
        year = start_date.year if start_date is not None else None
        men, women, indexes = await self.socdemo_client.get_population_pyramid(territory_id, oktmo_code, year)

        men_prob = [x / sum(men) for x in men]
        women_prob = [x / sum(women) for x in women]

        # todo add working indexes and solve 70-74 problem
        """
        [70-74] = 530 not single year population info

        70 71 72 73 74
        0.65x  0.6x 0.5x  0.4x  0.3x
        get survivability_coefficients


        2.35x = 530
        x = 225
        70   71  72 73 74
        146 135 112 90 67 = 530
        evaluate
        the problem is that you dont have surv_coeff in divide
        """
        primary = [SocialGroupWithProbability.from_values("people_pyramid", 1, men_prob, women_prob)]
        distribution = SocialGroupsDistribution(primary, [])

        return prdivide(
            territory_id=territory_id,
            houses_df=houses_df,
            distribution=distribution,
            year=year,
            working_db_path=self.divide_working_db_path,
            verbose=self.debug,
        )

    async def insert_forecasted_data(
        self,
        input_dir: str,
        territory_id: int,
        year_begin: int,
        years: int
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

        db_paths = [f"{input_dir}/year_{year}.sqlite" for year in range(year_begin + 1, year_begin + years + 1)]
        cur_year = year_begin + 1

        logger = structlog.get_logger()

        for db_path in db_paths:
            year_data = export_year_age_values(
                db_path=db_path,
                territory_id=territory_id,
                verbose=self.debug
            )

            logger.info(f"posting {db_path} data to the saving api")
            if year_data is None:
                logger.error(f"got no data from {db_path}")
                raise ObjectNotFoundError()

            buildings_data: list[UrbanSocialDistribution] = []
            for index, values in year_data.iterrows():
                buildings_data.append(
                    UrbanSocialDistribution(
                        building_id=values["house_id"],
                        scenario="NEUTRAL", # add scenario here
                        year=cur_year,
                        sex="MALE",
                        age=values["age"],
                        value=values["men"],
                    )
                )
                buildings_data.append(
                    UrbanSocialDistribution(
                        building_id=values["house_id"],
                        scenario="NEUTRAL",  # add scenario here
                        year=cur_year,
                        sex="FEMALE",
                        age=values["age"],
                        value=values["women"],
                    )
                )
            cur_year += 1
            #await self.saving_client.post_forecasted_data(buildings_data)
            with open("test.txt", 'w+') as file:
                for i in buildings_data:
                    file.write(str(i.dict()))
                    file.write('\n')

    async def restore(
        self,
        territory_id: int,
        survivability_coefficients: dict[str, tuple[float]],
        year_begin: int,
        years: int,
        boys_to_girls: float,
        fertility: FertilityPerWoman,
        scenario: tp.Literal["NEGATIVE", "NEUTRAL", "POSIVITE"],
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
            fertility:
                fertility_coefficient: float, births per woman each year value
                fertility_begin & fertility_end: int, age of beginning and stopping to giving birth
            from_scratch: bool, if true dividing first, otherwise using dividing data from divide output db
        """

        # example
        coeffs = SurvivabilityCoefficients(
            [1 / (i * 0.1) for i in range(1, 100)], [1 / (i * 0.1) for i in range(1, 100)]
        )

        fertility.adapt_to_scenario(scenario)

        if from_scratch:
            await self.divide(territory_id, start_date=date(year_begin,1,1))

        prforecast(
            houses_db=self.divide_working_db_path,
            territory_id=territory_id,
            coeffs=coeffs,  # should be replaced to survivability_coefficients
            year_begin=year_begin,
            years=years,
            boys_to_girls=boys_to_girls,
            fertility_coefficient=fertility.fertility_coefficient,
            fertility_begin=fertility.fertility_begin,
            fertility_end=fertility.fertility_end,
            verbose=self.debug,
            working_dir=self.forecast_working_dir_path,
        )

        await self.insert_forecasted_data(
            input_dir=self.forecast_working_dir_path,
            territory_id=territory_id,
            year_begin=year_begin,
            years=years
        )
