"""
Response models are defined here
"""

from typing import Optional

from pydantic import BaseModel, Field


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
    detail: str


class TimeoutErrorResponse(BaseModel):
    detail: str


class JobNotFoundErrorResponse(BaseModel):
    detail: str


class SurvivabilityCoefficients(BaseModel):
    men: tuple
    women: tuple
