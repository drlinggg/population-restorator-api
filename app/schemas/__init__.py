"""
Response schemas are defined here.
"""

from .ping import PingResponse
from .territories import (
    ErrorResponse,
    GatewayErrorResponse,
    JobCreatedResponse,
    JobErrorResponse,
    JobNotFoundErrorResponse,
    JobResponse,
    SurvivabilityCoefficients,
    TerritoryResponse,
    TimeoutErrorResponse,
    UrbanSocialDistributionPost,
)
