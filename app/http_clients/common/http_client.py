from __future__ import annotations

import abc

from app.utils import ApiConfig


class BaseClient(abc.ABC):
    """Base API client"""

    def __init__(self):
        self.config: ApiConfig | None = None

    @abc.abstractmethod
    async def is_alive(self) -> bool:
        """Check if urban_api instance is alive."""

    async def get_version(self) -> str | None:
        """Get API version if appliable."""
        return None
