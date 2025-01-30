"""Logging middleware is defined here"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils import logger


class LoggingMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Middleware for logging requests. Using `state.user` data and `state.logger` to log details."""

    def __init__(self, app):
        self.logger = logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # do something with the request object, for example
        self.logger.debug(f'got request: {dict(request.headers.items())["host"]}')

        # process the request and get the response
        response = await call_next(request)

        return response
