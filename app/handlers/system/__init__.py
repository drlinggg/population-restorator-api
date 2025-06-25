"""
All FastApi system handlers&routers are exported from this module.
"""

from .check_health import check_health
from .redirect_to_swagger import redirect_to_swagger_docs
from .routers import system_routers_list
