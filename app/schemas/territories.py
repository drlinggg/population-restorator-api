"""
Response models are defined here
"""

from typing import Optional

from pydantic import BaseModel, Field


class TerritoryResponse(BaseModel):
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class DebugErrorResponse(BaseModel):
    detail: str = "Exception occured"
    error: str
    error_type: str
    path: str
    trace: str


class DebugJobErrorResponse(BaseModel):
    detail: str = "Exception occured"
    job_id: str
    error: str
    error_type: str
    path: str
    trace: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[TerritoryResponse]


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str


class SurvivabilityCoefficients(BaseModel):
    men: tuple
    women: tuple
