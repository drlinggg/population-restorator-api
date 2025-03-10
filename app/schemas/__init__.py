"""
Response schemas are defined here.
"""

from .ping import PingResponse
from .territories import (
    DebugErrorResponse,
    JobCreatedResponse,
    JobResponse,
    JobErrorResponse,
    TerritoryBalanceResponse,
    TerritoryDivideResponse,
    TerritoryRestoreResponse,
)
