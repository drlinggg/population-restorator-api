from fastapi import FastAPI
import os
from api_app.handlers.routers import routers_list
from api_app.utils import read_db_env, read_api_env, UrbanApiConfig, DBConfig, try_load_envfile

def get_app(prefix: str = "/api") -> FastAPI:
    """todo"""
    desc = "todo"

    app = FastAPI(
            title="Population-restorator",
            description=desc,
            version="0.0.1",
            contact = {"name": "Banakh Andrei", "email": "uuetsukeu@mail.ru"},
            license_info={"name": "MIT"}
    )

    #todo get idea how to use it in services
    try_load_envfile(os.environ.get("ENVFILE", "urban_api.env"))
    urban_api_config = read_api_env()
    try_load_envfile(os.environ.get("ENVFILE", "db.env"))
    db_config = read_db_env()


    for route in routers_list:
        app.include_router(route, prefix=(prefix if "/" not in {r.path for r in route.routes} else ""))

    return app

app = get_app()
