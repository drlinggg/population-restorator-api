import abc
import json
import os
from dataclasses import dataclass

import pandas as pd
import structlog
from aiohttp import ClientConnectionError, ClientSession, ClientTimeout

from app.http_clients.common import (
    APIConnectionError,
    APITimeoutError,
    BaseClient,
    ObjectNotFoundError,
    handle_exceptions,
    handle_request,
)
from app.utils import PopulationRestoratorApiConfig


config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
logger = structlog.getLogger()

class SocDemoClient(BaseClient):

    def __init__(self):
        self.config: ApiConfig | None = config.urban_api

        if not (self.config.host.startswith("http")):
            logger.warning("http/https schema is not set, defaulting to http")
            self.config.host = f"http://{self.config.host}"

    def is_alive(self) -> bool:

        url = f"{self.config.host}{self.config.bash_path}/health_check/ping"

        result = handle_request(url)

        if result:
            return True

    def __str__(self):
        return "SocDemoClient"

    @handle_exceptions
    async def get_population_pyramid(territory_id: int):
        pass
