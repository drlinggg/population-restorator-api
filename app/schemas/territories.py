"""
Balance, divide, restore
responses are defined here
"""

from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


# todo unite these schemas
class TerritoryBalanceResponse(BaseModel):
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class TerritoryDivideResponse(BaseModel):
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class TerritoryRestoreResponse(BaseModel):

    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class DebugErrorResponse(BaseModel):
    error: str
    error_type: str
    path: str
    params: str
    trace: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[TerritoryBalanceResponse]

class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
