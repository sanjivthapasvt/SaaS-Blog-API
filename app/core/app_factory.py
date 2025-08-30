from fastapi import FastAPI

from app.core.config import settings
from app.core.docs import setup_docs_routes
from app.core.lifespan import lifespan
from app.core.middleware import setup_middleware
from app.core.routes import setup_routes
from app.core.static_files import setup_static_files


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
