import json

import pandas as pd

from app.utils import urban_api_config

from .requests import handle_request


async def get_houses_of_territory(territory_id: int) -> pd.DataFrame:
    pass
