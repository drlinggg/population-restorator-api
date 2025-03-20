"""All FastApi middlewares are defined here"""

from .dependency_injection import PassServicesDependenciesMiddleware
from .exception_handler import ExceptionHandlerMiddleware
from .logging import LoggingMiddleware
