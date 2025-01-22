from starlette import status

from app.helpers import get_current_time
from app.logic.territories import (
    TerritoriesService,
    get_territories_service,
)
from app.schemas import (
    TerritoryBalanceResponse,
    TerritoryDivideResponse,
    TerritoryRestoreResponse,
)

from .routers import territories_router


@territories_router.post(
    "/territories/balance/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=TerritoryBalanceResponse,
)
async def balance(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    # todo debug
    await territories_service.balance(territory_id)
    return TerritoryBalanceResponse(
        performed_at=get_current_time(), territory_id=territory_id
    )


@territories_router.post(
    "/territories/divide/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=TerritoryDivideResponse,
)
async def divide(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.divide(territory_id)
    return TerritoryDivideResponse(
        performed_at=get_current_time(), territory_id=territory_id
    )


@territories_router.post(
    "/territories/restore/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=TerritoryRestoreResponse,
)
async def restore(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.restore(territory_id)
    return TerritoryRestoreResponse(
        performed_at=get_current_time(), territory_id=territory_id
    )
