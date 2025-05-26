from pydantic import BaseModel
from typing import Literal

class UrbanSocialDistribution(BaseModel):
    building_id: int
    scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"]
    year: int
    sex: Literal["MALE", "FEMALE"]
    age: int
    value: int
