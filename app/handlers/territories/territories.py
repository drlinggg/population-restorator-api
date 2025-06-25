"""
FastApi territory & population related handlers are defined here
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal, Union

from fastapi import HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.http_clients.common.exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InvalidStatusCode,
    ObjectNotFoundError,
)
from app.schemas import (
    ErrorResponse,
    GatewayErrorResponse,
    JobCreatedResponse,
    JobErrorResponse,
    JobNotFoundErrorResponse,
    JobResponse,
    TerritoryResponse,
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
async def balance(
    request: Request,
    territory_id: int,
    start_date: date = Query(None, description="earliest date information about to be searched for"),
):
    # todo desc

    territories_service = request.app.state.territories_service

    job = request.app.state.queue.enqueue(
        territories_service.balance,
        args=(
            territory_id,
            start_date,
        ),
        job_timeout=9000,
    )
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
    start_date: date = Query(None, description="earliest date information about to be searched for"),  # NO TOGETHER
    from_previous: str = Query(None, description="id of balance job which calculations would be used"),
):
    # todo desc

    if start_date is not None and from_previous is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can use either start_date or from_previous",
        )

    territories_service = request.app.state.territories_service

    prev_job = request.app.state.queue.fetch_job(from_previous) if from_previous else None
    if from_previous is None:
        job = request.app.state.queue.enqueue(
            territories_service.divide, territory_id, start_date=start_date, job_timeout=9000
        )
    elif prev_job and prev_job.is_finished:
        job = request.app.state.queue.enqueue(
            territories_service.divide, territory_id, houses_df=prev_job.return_value()[1]
        )
    elif prev_job and not prev_job.is_finished:
        raise HTTPException(status_code=424, detail=f"Previous job {from_previous} is not finished yet.")
    else:
        return JSONResponse(
            JobNotFoundErrorResponse(detail="previous job {from_previous} not found").model_dump(), status_code=404
        )

    return JobCreatedResponse(job_id=job.id, status="Queued")


@territories_router.post(
    "/territories/restore/{territory_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=JobCreatedResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },  # todo
)
async def restore(
    request: Request,
    territory_id: int,
    year_begin: int = Query(...),
    year_end: int = Query(...),
    scenario: Literal["NEGATIVE", "NEUTRAL", "POSITIVE"] = "NEUTRAL",
    from_scratch: bool = Query(True, description="recalculate previous steps before restoring"),
):
    # todo desc
    territories_service = request.app.state.territories_service

    restore_args = {
        "territory_id": territory_id,
        "year_begin": year_begin,
        "years": year_end - year_begin,
        "scenario": scenario,
        "from_scratch": from_scratch,
    }

    job = request.app.state.queue.enqueue(territories_service.restore, kwargs=restore_args, job_timeout=9000)

    return JobCreatedResponse(job_id=job.id, status="Queued")


@territories_router.get(
    "/territories/status/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    responses={
        404: {"description": "Job not found", "model": JobNotFoundErrorResponse},
        500: {"description": "Internal Server Error", "model": ErrorResponse},
        502: {"description": "Bad Gateway", "model": Union[JobErrorResponse, GatewayErrorResponse]},
        504: {"description": "Didn't receive a timely response from upstream server", "model": TimeoutErrorResponse},
    },
)
async def get_status(request: Request, job_id: str):
    job = request.app.state.queue.fetch_job(job_id)

    if job is None:
        return JSONResponse(
            content=JobNotFoundErrorResponse(detail="No job with such id").model_dump(), status_code=404
        )

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
