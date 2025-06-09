from typing import Literal, Tuple

from pydantic import BaseModel, Field, ValidationError, model_validator, validator


class FertilityInterval(BaseModel):
    start: int = Field(gt=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def check_interval(self):
        if self.start > self.end:
            raise ValueError(
                f"Fertility beginning shouldn't be bigger than ending, " f"got {self.start} and {self.end} instead"
            )
        return self


class BirthStats(BaseModel):
    """
    This model is used to be changed by input scenario and passed as arguments in restore function
    fertility_interval is a ferility_begin & fertility_end interval in ages when women are giving birth
    ferility_coefficient is a probability to give a birth every year, for e.x.: baby_per_woman/(f_end-f_begin)
    """

    fertility_interval: FertilityInterval
    boys_to_girls: float = Field(gt=0)
    fertility_coefficient: float = Field(gt=0)

    def adapt_to_scenario(self, scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"]):
        if scenario == "NEGATIVE":
            self.fertility_interval.start = round(self.fertility_interval.start * 1.05)
            self.fertility_interval.end = round(self.fertility_interval.end * 0.95)
            self.fertility_coefficient *= 0.95
        elif scenario == "POSITIVE":
            self.fertility_interval.start = round(self.fertility_interval.start * 0.95)
            self.fertility_interval.end = round(self.fertility_interval.end * 1.05)
            self.fertility_coefficient *= 1.05


class SurvivabilityCoefficients(BaseModel):
    "This model is used to recreate next year population for all ages by multiplication it by men[age]/women[age]"

    men: Tuple[float, ...]
    women: Tuple[float, ...]
    year: int = Field(ge=1900)

    @validator("men", "women", each_item=True)
    def check_non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class PopulationPyramid(BaseModel):
    """
    This model is used in divide function
    and two models with 1 year gap could be used to recreate SurvivabilityCoefficients
    """

    men: Tuple[int, ...]
    women: Tuple[int, ...]
    year: int = Field(ge=1900)

    @validator("men", "women", each_item=True)
    def check_non_negative_int(cls, v):
        if v < 0:
            raise ValueError("Population value must be non-negative")
        return v
