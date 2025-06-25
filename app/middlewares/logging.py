"""Logging middleware is defined here"""

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Middleware for logging requests. Using `state.user` data and `state.logger` to log details."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4()
        logger: structlog.stdlib.BoundLogger = request.app.state.logger
        request.app.state.logger.info(f'got request: {{host: {dict(request.headers.items())["host"]}}}')

        response = await call_next(request)

        return response
