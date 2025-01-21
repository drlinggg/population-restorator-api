from fastapi import status
from fastapi.responses import RedirectResponse
from .routers import system_router

@system_router.get("/", status_code=status.HTTP_307_TEMPORARY_REDIRECT, include_in_schema=False)
async def redirect_to_swagger_docs():
    """Redirects to **/api/docs** from **/**"""
    return RedirectResponse("/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

