from pydantic import BaseModel
from typing import Literal

class FertilityPerWoman(BaseModel):
    fertility_begin: int = 18
    fertility_end: int = 40
    fertility_coefficient: float = 0.9

    def adapt_to_scenario(self, scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"]):
        if scenario == "NEGATIVE":
            self.fertility_begin = round(self.fertility_begin * 1.05)
            self.fertility_end = round(self.fertility_end * 0.95)
            self.fertility_coefficient *= 0.95
        elif scenario == "POSITIVE":
            self.fertility_begin = round(self.fertility_begin * 0.95)
            self.fertility_end = round(self.fertility_end * 1.05)
            self.fertility_coefficient *= 1.05


class SurvivabilityCoefficients(BaseModel):
    men: tuple
    women: tuple
    year: int


class PopulationPyramid(BaseModel):
    men: tuple
    women: tuple
    year: int
