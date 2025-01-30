# todo desc

from fastapi import FastAPI

from app.handlers.routers import routers_list


def get_app(prefix: str = "/api") -> FastAPI:
    desc = "todo"

    app = FastAPI(
        title="Population-restorator-api",
        description=desc,
        version="0.0.1",
        contact={"name": "Banakh Andrei", "email": "uuetsukeu@mail.ru"},
        license_info={"name": "MIT"},
    )

    for route in routers_list:
        app.include_router(route, prefix=(prefix if "/" not in {r.path for r in route.routes} else ""))

    return app


app = get_app()
