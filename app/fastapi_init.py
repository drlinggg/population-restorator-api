import dataclasses
import os
from contextlib import asynccontextmanager

import multiprocess as mp
from fastapi import FastAPI

from app.handlers.routers import routers_list
from app.http_clients import SavingClient, SocDemoClient, UrbanClient
from app.logic import TerritoriesService
from app.middlewares import (
    ExceptionHandlerMiddleware,
    LoggingMiddleware,
)
from app.utils import PopulationRestoratorApiConfig, configure_logging, start_redis_queue, start_rq_worker


def get_app(prefix: str = "/api") -> FastAPI:
    desc = "population-restorator-api, uses population-restorator module to forecast population for territories"

    app = FastAPI(
        title="Population-restorator-api",
        description=desc,
        version="1.0.1 blue mountain",
        contact={"name": "Banakh Andrei", "email": "uuetsukeu@mail.ru"},
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )
    app_config = PopulationRestoratorApiConfig.from_file_or_default(os.getenv("CONFIG_PATH"))
    app.state.config = app_config

    for route in routers_list:
        app.include_router(route, prefix=(prefix if "/" not in {r.path for r in route.routes} else ""))

    loggers_dict = {logger_config.filename: logger_config.level for logger_config in app_config.logging.files}
    logger = configure_logging(app_config.logging.level, loggers_dict)
    app.state.logger = logger

    app.add_middleware(
        LoggingMiddleware,
    )
    app.add_middleware(ExceptionHandlerMiddleware, debug=(app_config.app.debug,))

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan function.
    """
    app_config = app.state.config

    app.state.territories_service = TerritoriesService(
        urban_client=UrbanClient(app_config.urban_api),
        socdemo_client=SocDemoClient(app_config.socdemo_api),
        saving_client=SavingClient(app_config.saving_api),
        debug=app_config.app.debug,
        population_restorator_config=app_config.population_restorator,
    )

    # todo add manage amount of workers
    host, port, db, queue_name = dataclasses.astuple(app_config.redis_queue)
    app.state.redis, app.state.queue = start_redis_queue(host=host, port=port, db=db)

    rq_worker_process = mp.Process(target=start_rq_worker, args=(host, port, db, queue_name))
    rq_worker_process.start()

    yield

    rq_worker_process.terminate()


app = get_app()
