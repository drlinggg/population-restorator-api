import os

import pandas as pd
import structlog

from app.http_clients.common import (
    BaseClient,
    handle_exceptions,
    handle_request,
    ObjectNotFoundError,
)
from app.utils import PopulationRestoratorApiConfig, ApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()

class SocDemoClient(BaseClient):

    def __init__(self):
        self.config: ApiConfig | None = config.socdemo_api

        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    async def is_alive(self) -> bool:

        url = f"{self.config.host}{self.config.bash_path}/health_check/ping"

        result = await handle_request(url)

        if result:
            return True
        return False

    def __str__(self):
        return "SocDemoClient"

    @handle_exceptions
    async def get_population_pyramid(self, territory_id: int) -> tuple[list[int], list[int], list[str]]:
        """
        Args: territory_id
        Returns: 
        """

        indicator_id: str = "2" # for populaion

        # getting response

        url = f"{self.config.host}{self.config.base_path}/indicators/{indicator_id}/{territory_id}/detailed"

        params = {
            "territory_id": territory_id,
            "indicator_id": indicator_id,
        }

        headers = {
            "accept": "application/json",
        }

        data = await handle_request(url, params, headers)

        if data is None:
            raise ObjectNotFoundError()

        pyramids = pd.DataFrame(data)
        latest_pyramid = pyramids.loc[pyramids["year"] == max(pyramids["year"])].iloc[0]

        # formatting

        men: list[int] = list()
        women: list[int] = list()
        indexes: list[str] = list()

        #keyerror territory_id 2, okay 1

        for item in latest_pyramid["data"]:
            index_start, index_end, men_amount, women_amount = (item["age_start"],
                                                                item["age_end"] if item["age_end"] is not None else 130,
                                                                int(item["male"]) if item["male"] is not None else 0,
                                                                int(item["female"]) if item["female"] is not None else 0)

            men.append(men_amount)
            women.append(women_amount)
            indexes.append(index_start if index_start == index_end else f'{index_start}-{index_end}')

        return men, women, indexes
