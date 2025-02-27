"""
Balance, divide, restore
responses are defined here
"""

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class TerritoryBalanceResponse(BaseModel):
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories were balanced",
        examples=["7"],
    )
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class TerritoryDivideResponse(BaseModel):
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories were divided",
        examples=["7"],
    )
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class TerritoryRestoreResponse(BaseModel):
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories restored",
        examples=["7"],
    )
    performed_at: str = Field(..., description="time of finishing operation", examples=["22-01-2025 09:53:46"])
    # todo


class DebugErrorResponse(BaseModel):
    error: str
    error_type: str
    path: str
    params: str
    trace: str
