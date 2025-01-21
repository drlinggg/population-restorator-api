"""
health_check endpoint is defined here.
"""

from .routers import system_router
from starlette import status
from api_app.schemas import PingResponse
import asyncio
import time

@system_router.get("/check_health/ping",
                   status_code=status.HTTP_200_OK,
                   response_model=PingResponse,
)
async def check_health():
    await asyncio.sleep(1)
    return PingResponse(message="pong!")
