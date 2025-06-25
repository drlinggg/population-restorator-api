"""
Population-restorator-api package

It can be used to balance city houses population in 3 steps
and data used to be taken from urban_api
- settle people to dwellings useing total city population and houses living area,
- divide people in houses to ages and social groups using number of people and variances values to
- forecast the people number over the following years depending on scenario
"""

from .fastapi_init import app
