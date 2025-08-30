from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings


def setup_static_files(app: FastAPI) -> None:
    """Configure static file serving"""

    # Mount media files
    app.mount("/media", StaticFiles(directory=settings.media_directory), name="media")

    # Mount static files
    app.mount(
        "/static", StaticFiles(directory=settings.static_directory), name="static"
    )
