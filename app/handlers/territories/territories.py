"""FastApi territory related handlers are defined here"""

from datetime import datetime, timezone

from fastapi import HTTPException, Request, status

from app.http_clients.common.exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InvalidStatusCode,
    ObjectNotFoundError,
)
from app.logic import TerritoriesService, get_territories_service
from app.schemas import (
    DebugErrorResponse,
    DebugJobErrorResponse,
    JobCreatedResponse,
    JobResponse,
    TerritoryBalanceResponse,
    TerritoryDivideResponse,
    TerritoryRestoreResponse,
)
from app.utils import JobError

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
    },  # todo
)
async def balance(request: Request, territory_id: int):
    # todo desc

    territories_service: TerritoriesService = get_territories_service()
    job = request.app.state.queue.enqueue(territories_service.balance, territory_id)
    return JobCreatedResponse(job_id=job.id, status="Queued")


# @territories_router.post(
#    "/territories/divide/{territory_id}",
#    status_code=status.HTTP_201_CREATED,
#    response_model=TerritoryDivideResponse,
# )
# async def divide(request: Request, territory_id: int):
#    # todo desc
#    territories_service: TerritoriesService = get_territories_service()
#    await territories_service.divide(territory_id)
#
#    return TerritoryDivideResponse(performed_at=str(strftime("%d-%m-%Y %H:%M:%S", gmtime())), territory_id=territory_id)
#
#
# @territories_router.post(
#    "/territories/restore/{territory_id}",
#    status_code=status.HTTP_201_CREATED,
#    response_model=TerritoryRestoreResponse,
# )
# async def restore(request: Request, territory_id: int):
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
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "examples": {
                        "Job": {"value": {"detail": "Job not found"}},
                        "Territory": {
                            "value": {
                                "detail": "Given object or its data is not found, therefore further calculations are impossible"
                            }
                        },
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "examples": {
                        "Debug": {
                            "value": DebugErrorResponse(
                                error="Sample Error", error_type="ValueError", path="path", trace="Sample Trace"
                            ).dict()
                        },
                        "Default": {"value": {"detail": "exception occured"}},
                    }
                }
            },
        },
        502: {
            "description": "Bad Gateway",
            "content": {
                "application/json": {
                    "examples": {
                        "Population-restorator debug": {
                            "value": DebugJobErrorResponse(
                                job_id="adaa6536-aa1f-45e5-8cee-2cc03694ae8e",
                                error="Sample Error",
                                error_type="ValueError",
                                path="path",
                                trace="Sample Trace",
                            ).dict()
                        },
                        "Population-restorator default": {
                            "value": {"job_id": "adaa6536-aa1f-45e5-8cee-2cc03694ae8e", "detail": "Exception occured"}
                        },
                        "Couldn't connect to upstream server": {
                            "value": {"detail": "couldn't connect to upstream server"}
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service Unavailable",
            "content": {"application/json": {"examples": {"Default": {"value": {"detail": "Service Unavailable"}}}}},
        },
        504: {
            "description": "Didn't receive a timely response from upstream server",
            "content": {
                "application/json": {
                    "examples": {
                        "Default": {"value": {"detail": "Didn't receive a timely response from upstream server"}}
                    }
                }
            },
        },
    },
)
async def get_status(request: Request, job_id: str):
    job = request.app.state.queue.fetch_job(job_id)

    if job is None:
        raise HTTPException(404, detail="Job not found")

    if job.is_finished:
        print(type(datetime.now(timezone.utc)))
        return JobResponse(
            job_id=job.id,
            status=job.get_status(),
            result=TerritoryBalanceResponse(performed_at=str(datetime.now(timezone.utc))),
        )

    if job.is_failed:
        job.refresh()
        exc_type = job.meta["exc_type"]["exc_type"]
        exc_value = job.meta["exc_value"]["exc_value"]

        if exc_type in FOREIGN_API_EXCEPTIONS:
            raise exc_type(exc_value)

        raise JobError(job.id, exc_type, exc_value, job.exc_info)

    return JobResponse(job_id=job.id, status=job.get_status(), result=job.result)
