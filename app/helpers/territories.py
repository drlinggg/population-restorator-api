# todo desc

import json

import pandas as pd

from app.utils import urban_api_config

from .requests import handle_request


async def get_internal_territories(parent_id: int) -> pd.DataFrame:
    # todo desc
    url = f"{urban_api_config.host}{urban_api_config.base_path}/all_territories"

    params = {
        "parent_id": parent_id,
        "get_all_levels": "True",
    }

    headers = {
        "accept": "application/json",
    }

    data = await handle_request(url, params, headers)
    data = await data.json()
    internal_territories_df = pd.DataFrame(data)

    # clear properties except level and name
    for i in internal_territories_df["features"]:
        i["properties"] = {
            **{"level": i["properties"]["level"]},
            **{"name": i["properties"]["name"]},
        }

    return internal_territories_df


async def get_population_for_internal_territories(parent_id: int):
    # todo desc
    pass


async def get_territory_level(territory_id) -> int:
    # todo desc
    url = (
        f"{urban_api_config.host}{urban_api_config.base_path}/territory/{territory_id}"
    )

    headers = {
        "accept": "application/json",
    }
    response = await handle_request(url, headers=headers)

    data = json.loads(await response.text())
    return data["level"]


async def save_first_two_layers_of_internal_territories(
    territories: pd.DataFrame, level: int
):
    # todo desc

    pass
