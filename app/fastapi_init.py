# todo desc

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.handlers.routers import routers_list
from app.middlewares import LoggingMiddleware, ExceptionHandlerMiddleware
from app.utils import PopulationRestoratorApiConfig, configure_logging


def get_app(prefix: str = "/api") -> FastAPI:
    desc = "todo"

    app = FastAPI(
        title="Population-restorator-api",
        description=desc,
        version="0.0.1",
        contact={"name": "Banakh Andrei", "email": "uuetsukeu@mail.ru"},
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )

    for route in routers_list:
        app.include_router(route, prefix=(prefix if "/" not in {r.path for r in route.routes} else ""))

    app.add_middleware(
        LoggingMiddleware,
    )

    app.add_middleware(
        ExceptionHandlerMiddleware,
        [True], #tobechanged
    )

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan function.
    """
    app_config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
    loggers_dict = {logger_config.filename: logger_config.level for logger_config in app_config.logging.files}
    logger = configure_logging(app_config.logging.level, loggers_dict)
    app.state.logger = logger

    yield


app = get_app()
