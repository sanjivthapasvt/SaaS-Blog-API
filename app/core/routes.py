from fastapi import FastAPI

from app.auth.google_routes import router as google_auth_router
from app.auth.routes import router as auth_router
from app.blogs.comment_routes import router as comment_router
from app.blogs.routes import router as blog_router
from app.notifications.routes import router as notification_router
from app.realtime.routes import router as realtime_router
from app.users.routes import router as users_router


def setup_routes(app: FastAPI) -> None:
    """Configure all API routes"""

    # Health check endpoint
    @app.get("/ping", tags=["Ping"])
    async def ping_server():
        return {"ping": "pong"}

    # Include API routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(google_auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(blog_router, prefix="/api", tags=["Blog"])
    app.include_router(comment_router, prefix="/api", tags=["Comments"])
    app.include_router(notification_router, prefix="/api", tags=["Notification"])
    app.include_router(realtime_router, prefix="/api", tags=["Realtime"])
    app.include_router(users_router, prefix="/api", tags=["Users"])
