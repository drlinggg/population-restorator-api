"""
FastApi territory & population related handlers are defined here
"""

from datetime import datetime, timezone

from fastapi import HTTPException, Query, Request, status

from typing import Union

from app.http_clients.common.exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InvalidStatusCode,
    ObjectNotFoundError,
)
from app.logic import TerritoriesService
from app.schemas import (
    ErrorResponse,
    JobErrorResponse,
    JobCreatedResponse,
    JobResponse,
    SurvivabilityCoefficients,
    TerritoryResponse,
    GatewayErrorResponse,
    JobNotFoundErrorResponse,
    TimeoutErrorResponse,
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
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },  # todo
)
async def balance(request: Request, territory_id: int):
    # todo desc

    # todo add these to middlewares with config by default
    territories_service = TerritoriesService()

    job = request.app.state.queue.enqueue(territories_service.balance, args=(territory_id,), job_timeout=500)
    return JobCreatedResponse(job_id=job.id, status="Queued")


@territories_router.post(
    "/territories/divide/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=JobCreatedResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        424: {"description": "Previous job is not finished yet"},
        404: {"model": JobNotFoundErrorResponse, "description": "Previous job not found"},
    },  # todo
)
async def divide(
    request: Request,
    territory_id: int,
    from_previous: str = Query(None, description="id of balance job which calculations would be used"),
):
    # todo desc
    # todo add these to middlewares with config by default
    territories_service = TerritoriesService()

    prev_job = request.app.state.queue.fetch_job(from_previous) if from_previous else None
    if from_previous is None:
        job = request.app.state.queue.enqueue(territories_service.divide, territory_id)
    elif prev_job and prev_job.is_finished:
        job = request.app.state.queue.enqueue(territories_service.divide, territory_id, prev_job.return_value()[1])
    elif prev_job and not prev_job.is_finished:
        raise HTTPException(status_code=424, detail=f"Previous job {from_previous} is not finished yet.")
    else:
        raise HTTPException(status_code=404, detail=f"Previous job {from_previous} not found.")

    return JobCreatedResponse(job_id=job.id, status="Queued")


@territories_router.post(
    "/territories/restore/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=JobCreatedResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        424: {"description": "Previous job is not finished yet"},
        404: {"model": JobNotFoundErrorResponse, "description": "Previous job not found"},
    },  # todo
)
async def restore(
    request: Request,
    territory_id: int,
    survivability_coefficients: SurvivabilityCoefficients,
    year_begin: int = Query(...),  # todo сделать чтобы это использовалось и бралось красиво
    year_end: int = Query(...),
    boys_to_girls: float = Query(...),
    fertility_coefficient: float = Query(...),
    fertility_begin: int = Query(18, description="age of fertility begining"),
    fertility_end: int = Query(38, description="age of fertility ending"),
    from_scratch: bool = Query(True, description="recalculate previous steps before restoring"),
):
    # todo desc
    territories_service = TerritoriesService()

    restore_args = (
        territory_id,
        survivability_coefficients,
        year_begin,
        year_end-year_begin,
        boys_to_girls,
        fertility_coefficient,
        fertility_begin,
        fertility_end,
        from_scratch,
    )

    job = request.app.state.queue.enqueue(territories_service.restore, args=restore_args)

    return JobCreatedResponse(job_id=job.id, status="Queued")


@territories_router.get(
    "/territories/status/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    responses={
        404: {
            "description": "Job not found",
            "model": JobNotFoundErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": ErrorResponse
        },
        502: {
            "description": "Bad Gateway",
            "model": Union[JobErrorResponse, GatewayErrorResponse]
        },
        504: {
            "description": "Didn't receive a timely response from upstream server",
            "model": TimeoutErrorResponse
        },
    },
)
async def get_status(request: Request, job_id: str):
    job = request.app.state.queue.fetch_job(job_id)

    if job is None:
        return JobNotFoundErrorResponse(detail=job_id)

    if job.is_finished:
        return JobResponse(
            job_id=job.id,
            status=job.get_status(),
            result=TerritoryResponse(performed_at=str(datetime.now(timezone.utc))),
        )

    if job.is_failed:
        exc_type = job.meta["exc_type"]["exc_type"]
        exc_value = job.meta["exc_value"]["exc_value"]

        if exc_type in FOREIGN_API_EXCEPTIONS:
            raise exc_type(exc_value)

        raise JobError(job.id, exc_type, exc_value, job.exc_info)

    return JobResponse(job_id=job.id, status=job.get_status(), result=job.result)
