from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.blogs.router import router as blog_router
from app.notifications.routes import router as notification_router
from app.realtime.routes import router as realtime_router
from app.users.router import router as users_router
from app.admin.router import router as admin_router

def setup_routes(app: FastAPI) -> None:
    """Configure all API routes"""

    # Health check endpoint
    @app.get("/ping", tags=["Ping"])
    async def ping_server():
        return {"ping": "pong"}

    # Include API routers
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(blog_router, prefix="/api")
    app.include_router(notification_router, prefix="/api", tags=["Notification"])
    app.include_router(realtime_router, prefix="/api", tags=["Realtime"])
    app.include_router(users_router, prefix="/api")
    app.include_router(admin_router, prefix="/admin")
