# todo desc

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class TerritoryBalanceResponse(BaseModel):
    performed_at: str = Field(
        ..., description="operation executed time", examples=["22-01-2025 09:53:46"]
    )
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories were balanced",
        examples=["7"],
    )
    # todo


class TerritoryDivideResponse(BaseModel):
    performed_at: str = Field(
        ..., description="operation executed time", examples=["22-01-2025 09:53:46"]
    )
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories were divided",
        examples=["7"],
    )
    # todo


class TerritoryRestoreResponse(BaseModel):
    performed_at: str = Field(
        ..., description="operation executed time", examples=["22-01-2025 09:53:46"]
    )
    territory_id: int = Field(
        ...,
        gt=0,
        description="id of territory that inner territories restored",
        examples=["7"],
    )
    # todo
