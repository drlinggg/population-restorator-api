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
    handle_request,
)
from app.utils import PopulationRestoratorApiConfig


# config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))


class SocDemoClient(BaseClient):
    pass
