"""
FastApi territory routers are defined here.
It is needed to import files which use these routers to initialize handlers.
"""

from fastapi import APIRouter


territories_router = APIRouter(tags=["territories"])

routers_list = [territories_router]

all = [
    "routers_list",
]
