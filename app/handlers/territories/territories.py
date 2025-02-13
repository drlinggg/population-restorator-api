"""FastApi territory related handlers are defined here"""

from time import gmtime, strftime

from fastapi import HTTPException, status
from starlette import status

from app.logic.territories import TerritoriesService, get_territories_service
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
    # idk mb do it another way
    responses={
        502: {"description": "Error contacting external service"},
    },
)
async def balance(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    # todo add debug
    result = await territories_service.balance(territory_id)

    # tobechanged IDK!
    if result:
        return TerritoryBalanceResponse(
            performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id
        )
    else:
        raise HTTPException(status_code=500, detail="Error contacting external service")


@territories_router.post(
    "/territories/divide/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=TerritoryDivideResponse,
)
async def divide(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.divide(territory_id)
    return TerritoryDivideResponse(performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id)


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
        performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id
    )
