"""FastApi territory related handlers are defined here"""

from time import gmtime, strftime

from fastapi import HTTPException, Request, status

from fastapi.responses import JSONResponse

from app.http_clients.common.exceptions import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    ObjectNotFoundError,
    InvalidStatusCode,
)

from starlette import status

from app.logic import TerritoriesService, get_territories_service
from app.schemas import (
    DebugErrorResponse,
    JobCreatedResponse,
    JobResponse,
    TerritoryBalanceResponse,
    TerritoryDivideResponse,
    TerritoryRestoreResponse,
)

from .routers import territories_router

FOREIGN_API_EXCEPTIONS = [
    APIError,
    APIConnectionError,
    APITimeoutError,
    ObjectNotFoundError,
    InvalidStatusCode,
]


@territories_router.post(
    "/territories/balance/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=JobCreatedResponse,
    responses={
        500: {"model": DebugErrorResponse, "description": "Internal Server Error"},
    },
)
async def balance(request: Request, territory_id: int):
    # todo desc

    territories_service: TerritoriesService = get_territories_service()
    job = request.app.state.queue.enqueue(territories_service.balance, territory_id)
    return JobCreatedResponse(job_id=job.id, status="Queued")


#@territories_router.post(
#    "/territories/divide/{territory_id}",
#    status_code=status.HTTP_201_CREATED,
#    response_model=TerritoryDivideResponse,
#)
#async def divide(request: Request, territory_id: int):
#    # todo desc
#    territories_service: TerritoriesService = get_territories_service()
#    await territories_service.divide(territory_id)
#
#    return TerritoryDivideResponse(performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id)
#
#
#@territories_router.post(
#    "/territories/restore/{territory_id}",
#    status_code=status.HTTP_201_CREATED,
#    response_model=TerritoryRestoreResponse,
#)
#async def restore(request: Request, territory_id: int):
#    # todo desc
#    territories_service: TerritoriesService = get_territories_service()
#    await territories_service.restore(territory_id)
#
#    return TerritoryRestoreResponse(
#        performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id
#    )

@territories_router.get(
    "/territories/status/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    responses={
        404: {"description": "Job not found"},
        500: {"model": DebugErrorResponse, "description": "Internal Server Error"},
        502: {"description": "Couldn't connect to urban_api"},
        503: {"description": "Service Unavailable"},
        504: {"description": "Didn't receive a timely response from upstream server"},
    },
)
async def get_status(request: Request, job_id: str):
    job = request.app.state.queue.fetch_job(job_id)

    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    if job.is_finished:
        return JobResponse(
            job_id=job.id,
            status=job.get_status(),
            result=TerritoryBalanceResponse(
                performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime()))
            ),
        )

    if job.is_failed:
        job.refresh()
        exc_type = job.meta["exc_type"]["exc_type"]
        exc_value = job.meta["exc_value"]["exc_value"]
    
        if exc_type in FOREIGN_API_EXCEPTIONS:
            raise exc_type(exc_value, job.id)

        raise Exception(exc_value)

    return JobResponse(job_id=job.id, status=job.get_status(), result=job.result)
