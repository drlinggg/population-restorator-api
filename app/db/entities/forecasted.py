import enum

from sqlalchemy import Column, Enum, Integer, SmallInteger, Table

from app.db import metadata


class ScenarioEnum(enum.Enum):
    NEGATIVE = 1
    NEUTRAL = 2
    POSITIVE = 3


class SexEnum(enum.Enum):
    MALE = 1
    FEMALE = 2


t_forecasted = Table(
    "divide",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("building_id", Integer, nullable=False),
    Column("scenario", Enum(ScenarioEnum), nullable=False),
    Column("year", Integer, nullable=False),
    Column("sex", Enum(SexEnum), nullable=False),
    Column("age", SmallInteger, nullable=False),
    Column("value", Integer, nullable=False),
)
""" Forecasted houses with people's amount by age and sex

Columns:
- 'id' - identifier, Integer
- 'building_id' - building indentifier, Integer
- 'scenario' - forecast scenario, NEGATIVE/NEUTRAL/POSITIVE Enum
- 'year' - year which used to be forecasted, Integer
- 'sex' - MALE/FEMALE Enum
- 'age' - age which used to be forecasted, SmallInteger
- 'value' - amount of people in building at this year who have such sex and age
"""
