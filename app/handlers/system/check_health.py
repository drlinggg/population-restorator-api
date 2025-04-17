"""
health_check handler is defined here.
"""

from starlette import status

from app.schemas import PingResponse

from .routers import system_router


@system_router.get(
    "/check_health/ping",
    status_code=status.HTTP_200_OK,
    response_model=PingResponse,
)
async def check_health():
    return PingResponse(message="pong!")
