# todo desc

import httpx

from api_app.utils import urban_api_config


async def get_territories_tree(territory_id: int):
    # todo return graph["territory"]

    url = f"{urban_api_config.host}{urban_api_config.base_path}/territories_without_geometry"
    # todo mb save in another place
    params = {
        "parent_id": territory_id,
        "get_all_levels": True,
        "cities_only": False,
        "ordering": "asc",
        "page": 1,
        "page_size": 10,
    }

    headers = {
        "accept": "application/json",
        # "Authorization": f"Bearer {urban_api_config.api_key}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        print(response.text)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    pass
