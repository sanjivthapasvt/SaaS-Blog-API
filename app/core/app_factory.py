from fastapi import FastAPI

from app.core.app_components.docs import setup_docs_routes
from app.core.app_components.lifespan import lifespan
from app.core.app_components.middleware import setup_middleware
from app.core.app_components.routes import setup_routes
from app.core.app_components.static_files import setup_static_files
from app.core.services.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI app"""

    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None,  # Disabled to use custom docs
        redoc_url=None,  # Disabled to use custom redoc
    )

    # Setup components
    setup_static_files(app)
    setup_middleware(app)
    setup_docs_routes(app)
    setup_routes(app)

    return app
