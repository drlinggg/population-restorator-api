from app.handlers.system import system_routers_list
from app.handlers.territories import routers_list as territories_routers_list

routers_list = [
    *territories_routers_list,
    *system_routers_list,
]

all = [
    "routers_list",
]
