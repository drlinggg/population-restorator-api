from starlette import status

from api_app.logic.impl.territories import get_territories_service
from api_app.logic.territories import TerritoriesService

from .routers import territories_router


@territories_router.post(
    "/territories/balance/{territory_id}",
    # response_model statuscode
)
async def balance(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.balance(territory_id)
    return f"test {territory_id}"


@territories_router.post(
    "/territories/divide/{territory_id}",
    # response_model statuscode
)
async def divide(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.divide(territory_id)
    return f"test {territory_id}"


@territories_router.post(
    "/territories/restore/{territory_id}",
    # response_model statuscode
)
async def restore(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.restore(territory_id)
    return f"test {territory_id}"
