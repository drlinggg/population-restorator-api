from fastapi import APIRouter

territories_router = APIRouter(tags=["territories"])

routers_list = [
        territories_router
]

all = [
    "routers_list",
]
