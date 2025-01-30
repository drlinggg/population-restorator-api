"""
All FastApi routers are defined here.

It is needed to import files which use these routers to initialize handlers.
"""

from app.handlers.system import system_routers_list
from app.handlers.territories import routers_list as territories_routers_list


routers_list = [
    *territories_routers_list,
    *system_routers_list,
]

all = [
    "routers_list",
]
