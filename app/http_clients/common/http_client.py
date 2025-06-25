"""Base API client is defined here"""

from __future__ import annotations

import abc

from app.utils import ApiConfig


class BaseClient(abc.ABC):
    """Base API client"""

    def __init__(self, api_config: ApiConfig):
        self.config: ApiConfig = api_config

    @abc.abstractmethod
    def __str__(self):
        """"""
