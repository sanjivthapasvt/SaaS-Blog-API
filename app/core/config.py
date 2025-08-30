from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Settings
    app_name: str = "SaaS-Blog-API"
    app_description: str = "This is API endpoints for SaaS-Blog-API"
    app_version: str = "1.0.0"

    # CORS Settings
    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "*",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Static Files Settings
    media_directory: str = "media"
    static_directory: str = "static"

    # Documentation Settings
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    favicon_url: str = "/static/favicon.ico"

    # Environment
    environment: str = "development"
    debug: bool = True

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


# Create settings instance
settings = Settings()
