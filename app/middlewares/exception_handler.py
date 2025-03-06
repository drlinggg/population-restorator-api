"""Exception handling middleware is defined here."""

import itertools
import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.http_clients.common import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    ObjectNotFoundError,
)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    todo
    """

    def __init__(self, app, debug: list[bool]):
        """
        Passing debug as a list with single element is a hack to be able to change the value
        on the application startup.
        """
        super().__init__(app)
        self._debug = debug

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except APIConnectionError as exc:
            return JSONResponse(status_code=502, content={"detail": "Couldn't connect to urban_api"})
        except APITimeoutError as exc:
            return JSONResponse(
                status_code=504, content={"detail": "Didn't receive a timely response from upstream server"}
            )
        except ObjectNotFoundError as exc:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Given object or its data is not found, therefore further calculations are impossible."
                },
            )
        except APIError as exc:
            return JSONResponse(status_code=503, content={"detail": "todo"})

        except Exception as exc:  # pylint: disable=broad-except
            error_status = 500
            if isinstance(exc, (APIError, HTTPException)):
                error_status = getattr(exc, "status_code", 500)

            if self._debug[0]:
                return JSONResponse(
                    {
                        "error": str(exc),
                        "error_type": str(type(exc)),
                        "path": request.url.path,
                        "params": request.url.query,
                        "trace": list(
                            itertools.chain.from_iterable(
                                map(lambda x: x.split("\n"), traceback.format_tb(exc.__traceback__))
                            )
                        ),
                    },
                    status_code=error_status,
                )
            return JSONResponse({"message": "exception occured"}, status_code=error_status)
