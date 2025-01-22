# todo desc

from app.utils import urban_api_config

from .requests import handle_request


async def get_territories_tree(territory_id: int):
    url = f"{urban_api_config.host}{urban_api_config.base_path}/all_territories"

    params = {
        "parent_id": territory_id,
        "get_all_levels": "True",
    }

    headers = {
        "accept": "application/json",
    }

    response = await handle_request(url, params, headers)

    """magic happens here"""

    """return magic"""

    pass
