"""
Response schemas are defined here.
"""

from .ping import PingResponse
from .territories import (
    ErrorResponse,
    JobErrorResponse,
    JobCreatedResponse,
    JobResponse,
    SurvivabilityCoefficients,
    TerritoryResponse,
    GatewayErrorResponse,
    JobNotFoundErrorResponse,
    TimeoutErrorResponse,
)
