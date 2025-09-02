from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

from app.core.services.config import settings


def setup_docs_routes(app: FastAPI) -> None:
    """Configure custom documentation routes."""

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,  # type: ignore
            title=f"API Documentation for {settings.app_name}",
            swagger_favicon_url=settings.favicon_url,
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,  # type: ignore
            title=f"API Documentation for {settings.app_name} - ReDoc",
            redoc_favicon_url=settings.favicon_url,
        )
