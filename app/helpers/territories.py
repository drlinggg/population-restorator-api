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
            **{"parent_id": i["properties"]["parent_id"]},
            **{"territory_id": i["properties"]["territory_id"]},
        }

    return internal_territories_df


async def get_population_for_internal_territories(parent_id: int) -> pd.DataFrame:
    # todo desc

    url = f"{urban_api_config.host}{urban_api_config.base_path}/territory/indicator_values"

    params = {
        "parent_id": parent_id,
        "indicators_ids": 1,
        "last_only": "true",
    }

    headers = {
        "accept": "application/json",
    }

    data = await handle_request(url, params, headers)
    data = await data.json()
    values = pd.DataFrame(data)
    return values


async def bind_population_to_territories(
    it: pd.DataFrame, ot: pd.DataFrame, parent_id: int
) -> (pd.DataFrame, pd.DataFrame):
    # todo desc

    population = await get_population_for_internal_territories(parent_id)

    for i in range(len(population["features"])):
        for j in range(len(it["features"])):
            if (
                population["features"][i]["properties"]["territory_id"]
                == it["features"][j]["properties"]["territory_id"]
            ):
                it["features"][j]["properties"]["population"] = population["features"][
                    i
                ]["properties"]["indicators"][0]["value"]

    for i in range(len(population["features"])):
        for j in range(len(ot["features"])):
            if (
                population["features"][i]["properties"]["territory_id"]
                == ot["features"][j]["properties"]["territory_id"]
            ):
                ot["features"][j]["properties"]["population"] = population["features"][
                    i
                ]["properties"]["indicators"][0]["value"]

    return (it, ot)


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
) -> (pd.DataFrame, pd.DataFrame):

    # todo desc
    columns = ["type", "features"]
    inner_territories_df = pd.DataFrame(columns=columns)
    outer_territories_df = pd.DataFrame(columns=columns)

    for i in range(len(territories)):
        if territories["features"][i]["properties"]["level"] - level == 1:
            outer_territories_df = pd.concat(
                [outer_territories_df, pd.DataFrame([territories.iloc[i]])],
                ignore_index=True,
            )

        elif territories["features"][i]["properties"]["level"] - level == 2:
            inner_territories_df = pd.concat(
                [inner_territories_df, pd.DataFrame([territories.iloc[i]])],
                ignore_index=True,
            )

    return (outer_territories_df, inner_territories_df)


async def bind_inners_to_outers(
    it: pd.DataFrame, ot: pd.DataFrame
) -> (pd.DataFrame, pd.DataFrame):
    # todo desc
    for i in range(len(it)):
        for o in range(len(ot)):
            if (
                it["features"][i]["properties"]["parent_id"]
                == ot["features"][o]["properties"]["territory_id"]
            ):
                it["features"][i]["properties"]["outer_territory"] = ot["features"][o][
                    "properties"
                ]["name"]
                break

    return (it, ot)

async def pretty_format(
    it: pd.DataFrame, ot: pd.DataFrame
) -> (pd.DataFrame, pd.DataFrame):
    #todo desc
    
    ot_columns = ['name', 'population', 'geometry']
    it_columns = ['name', 'population', 'outer_territory', 'geometry']

    outer_territories_df = pd.DataFrame(columns=ot_columns)
    inner_territories_df = pd.DataFrame(columns=it_columns)

    for i in range(len(it)):
        inner_territories_df.loc[len(inner_territories_df)] = [it['features'][i]['properties']['name'],
                                                               it['features'][i]['properties']['population'],
                                                               it['features'][i]['properties']['outer_territory'],
                                                               it['features'][i]['geometry']]

    for i in range(len(ot)):
        outer_territories_df.loc[len(outer_territories_df)] = [ot['features'][i]['properties']['name'],
                                                               ot['features'][i]['properties']['population'],
                                                               ot['features'][i]['geometry']]

    print(inner_territories_df)
    print(outer_territories_df)
    return (it, ot)

