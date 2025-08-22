import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter

from app.auth.google_auth import router as google_auth_router
from app.auth.routes import router as auth_router
from app.auth.security import TokenBlacklist
from app.blogs.comment_routes import router as comment_router
from app.blogs.routes import router as blog_router
from app.core.database import init_db
from app.core.redis import redis_manager
from app.notifications.routes import router as notification_router
from app.realtime.manager import sse_manager
from app.realtime.routes import router as realtime_router
from app.users.routes import router as users_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    testing = os.environ.get("TESTING") == "1"
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Connect Redis using the manager
    await redis_manager.connect(testing=testing, redis_url=redis_url)
    redis_connection = redis_manager.get_client()

    # Initialize FastAPI Limiter
    await FastAPILimiter.init(redis_connection)
    await init_db()

    # store redis in app.state
    app.state.redis = redis_connection
    app.state.token_blacklist = TokenBlacklist(redis_connection)  # type: ignore
    app.state.redis_manager = redis_manager

    # Start SSE Redis listener (if not testing or if you want to test SSE)
    listener_task = None
    if not testing or os.environ.get("TEST_SSE") == "1":
        listener_task = asyncio.create_task(
            sse_manager.start_redis_listener(redis_manager)
        )

    yield

    # Cleanup
    if listener_task:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass

    await redis_manager.disconnect()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(google_auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(blog_router, prefix="/api", tags=["Blog"])
app.include_router(comment_router, prefix="/api", tags=["Comments"])
app.include_router(notification_router, prefix="/api", tags=["Notification"])
app.include_router(realtime_router, prefix="/api", tags=["Realtime"])
app.include_router(users_router, prefix="/api", tags=["Users"])
