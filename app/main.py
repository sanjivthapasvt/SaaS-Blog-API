from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.auth.routes import router as auth_router
from app.auth.google_auth import router as google_auth_router
from app.blogs.routes import router as blog_router
from app.blogs.comment_routes import router as comment_router
from app.notifications.routes import router as notification_router
from app.users.routes import router as users_router
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from fakeredis import FakeAsyncRedis

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = redis.from_url("redis://localhost:6379", encoding="utf8")
    testing = os.environ.get("TESTING") == "1"
    
    if testing:
        redis_connection = FakeAsyncRedis()
    
    await FastAPILimiter.init(redis_connection)
    await init_db()
    yield
    await redis_connection.aclose()

    
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(google_auth_router, prefix="/auth", tags=["Auth"])
app.include_router(blog_router, prefix="/api", tags=["Blog"])
app.include_router(comment_router, prefix="/api", tags=["Comments"])
app.include_router(notification_router, prefix="/api", tags=["Notification"])
app.include_router(users_router, prefix="/api", tags=["Users"])