"""
Response models are defined here
"""

from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.models import UrbanSocialDistribution


class TerritoryResponse(BaseModel):
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])


class ErrorResponse(BaseModel):
    detail: str = "Exception occured"
    error: Optional[str] = None
    error_type: Optional[str] = None
    path: Optional[str] = None
    trace: Optional[str] = None


class JobErrorResponse(BaseModel):
    detail: str = "Exception occured in job execution"
    job_id: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    path: Optional[str] = None
    trace: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[TerritoryResponse]


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str


class GatewayErrorResponse(BaseModel):
    detail: str = "did not get a response from the upstream server in order to complete the request"


class TimeoutErrorResponse(BaseModel):
    detail: str = "did not get a response in time from the upstream server in order to complete the request"


class JobNotFoundErrorResponse(BaseModel):
    detail: str = "job not found"


class SurvivabilityCoefficients(BaseModel):
    men: tuple
    women: tuple


class UrbanSocialDistributionPost(BaseModel):
    building_id: int
    scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"]
    year: int
    sex: Literal["MALE", "FEMALE"]
    age: int
    value: int

    @classmethod
    def from_model(model: UrbanSocialDistribution):
        return UrbanSocialDistributionPost(**model.model_dump())
