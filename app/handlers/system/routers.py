"""
Api system routers are defined here.
It is needed to import files which use these routers to initialize handlers.
"""

from fastapi import APIRouter


system_router = APIRouter(tags=["system"])

system_routers_list = [
    system_router,
]

all = ["system_routers_list,"]
