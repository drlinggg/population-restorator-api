from typing import Literal

from pydantic import BaseModel, Field


class UrbanSocialDistribution(BaseModel, frozen=True):
    """
    This model is used to be forecasted in forecast function
    Used to be sent to saving_api as a list[UrbanSocDistr] result of forecast end-point
    """

    building_id: int = Field(ge=0)
    scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"]
    year: int = Field(ge=1900)
    sex: Literal["MALE", "FEMALE"]
    age: int = Field(ge=0, le=100)
    value: int = Field(ge=0)
