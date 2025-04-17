"""
TerritoriesService is defined here
it is used for getting necessary data by using http clients
and perfom population-restorator library executing
"""

from __future__ import annotations

import asyncio
import typing as tp

import pandas as pd
from population_restorator.forecaster import export_year_age_values
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability, SurvivabilityCoefficients

# torename
from population_restorator.scenarios import balance as prbalance
from population_restorator.scenarios import divide as prdivide
from population_restorator.scenarios import forecast as prforecast

from app.http_clients import (
    SocDemoClient,
    UrbanClient,
)


# add this to middleware
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
        debug: bool,
        forecast_working_dir_path: str,
        divide_working_db_path: str,
    ):

        self.urban_client = urban_client
        self.socdemo_client = socdemo_client
        self.debug = debug
        self.forecast_working_dir_path = forecast_working_dir_path
        self.divide_working_db_path = divide_working_db_path

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

        internal_territories_df = await self.urban_client.get_internal_territories(territory_id)

        internal_territories_df, internal_houses_df, population, main_territory = await asyncio.gather(
            self.urban_client.bind_population_to_territories(internal_territories_df),
            self.urban_client.get_houses_from_territories(territory_id),
            self.urban_client.get_population_from_territory(territory_id),
            self.urban_client.get_territory(territory_id),
        )

        # internal_territories_df.to_csv("population-restorator/sample_data/balancer/territories.csv")
        # internal_houses_df.to_csv("population-restorator/sample_data/balancer/houses.csv")

        return prbalance(
            population,
            internal_territories_df,
            internal_houses_df,
            main_territory,
            self.debug,
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

        men, women, indexes = await self.socdemo_client.get_population_pyramid(territory_id)

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

        if houses_df is None:
            houses_df = (await self.balance(territory_id))[1]

        return prdivide(
            territory_id=territory_id,
            houses_df=houses_df,
            distribution=distribution,
            year=None,
            verbose=self.debug,
            working_db_path=self.divide_working_db_path,
        )

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
            houses_db=self.divide_working_db_path,  # toberenamed
            territory_id=territory_id,
            coeffs=coeffs,  # should be replaced to survivability_coefficients
            year_begin=year_begin,
            years=years,
            boys_to_girls=boys_to_girls,
            fertility_coefficient=fertility_coefficient,
            fertility_begin=fertility_begin,
            fertility_end=fertility_end,
            verbose=self.debug,
            working_dir=self.forecast_working_dir_path,
        )

        # save here
