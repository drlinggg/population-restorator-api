"""FastApi territory related handlers are defined here"""

from time import gmtime, strftime

from fastapi import HTTPException, status
from starlette import status

from app.logic.territories import TerritoriesService, get_territories_service
from app.schemas import (
    TerritoryBalanceResponse,
    TerritoryDivideResponse,
    TerritoryRestoreResponse,
    DebugErrorResponse,
)

from .routers import territories_router


@territories_router.post(
    "/territories/balance/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=TerritoryBalanceResponse,
    responses={
        404: {"description": "Given object or its data is not found, therefore further calculations are impossible."},
        500: {"model": DebugErrorResponse, "description": "Internal Server Error"},
        502: {"description": "Couldn't connect to urban_api"}, 
        503: {"description": "Service Unavailable"},
        504: {"description": "Didn't receive a timely response from upstream server"}
    }
)
async def balance(territory_id: int):
    # todo desc
    territories_service: TerritoriesService = get_territories_service()
    await territories_service.balance(territory_id)

    return TerritoryBalanceResponse(
                performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), 
                territory_id=territory_id
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
            performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), 
            territory_id=territory_id
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
        performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), 
        territory_id=territory_id
    )
