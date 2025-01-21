from fastapi import APIRouter

system_router = APIRouter(tags=['system'])

system_routers_list = [
    system_router,
]

all = [
    "system_routers_list,"
]
