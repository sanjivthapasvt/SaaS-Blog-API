import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.app_components.logging_middleware import LoggingMiddleware
from app.core.services.config import settings


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the FastAPI application."""

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Trusted Host Middleware for production
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[os.getenv("ALLOWED_HOSTS") or ""]
        )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Logging Middleware
    app.add_middleware(LoggingMiddleware)
